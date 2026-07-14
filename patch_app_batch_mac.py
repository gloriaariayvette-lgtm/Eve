#!/usr/bin/env python3
"""patch_app_batch_mac.py — RUN ON THE MAC in the vintos repo. Patches vintos-app/src/index.html:
  #2 GCS button  -> use API base + secret (was a bare relative URL that never left the phone)
  #6 flicker     -> forward live emotional color into the avatar glow (_avTargetColor)
  #1 keep-msgs   -> persist last avatar-overlay messages, show a few, reappear on reopen
Backs up first, anchored (aborts cleanly if the file differs — nothing half-written), prints a diff.
Does NOT touch device-stop, toy_link.py, or the emote/T-pose player. Review the diff, then rebuild.
"""
import os, sys, difflib

CANDS = [
    "vintos-app/src/index.html",
    "src/index.html",
    os.path.expanduser("~/vintos-repo/vintos-app/src/index.html"),
    os.path.expanduser("~/Vintos/vintos-app/src/index.html"),
]
def find_file():
    for c in CANDS:
        if os.path.exists(c): return c
    for base, _, files in os.walk("."):
        if "node_modules" in base or "/ios/" in base or "/build" in base: continue
        if "index.html" in files and base.replace("\\", "/").endswith("vintos-app/src"):
            return os.path.join(base, "index.html")
    return None

path = find_file()
if not path:
    print("!! could not find vintos-app/src/index.html — run me from inside the vintos repo."); sys.exit(1)
print("target:", path)
src = open(path, encoding="utf-8").read()
orig = src

E = "…"  # ellipsis, exactly as in the file

# ---- edits: (label, old, new) ; each old must appear exactly once ----
edits = []

# #2 GCS button — use API base + secret header, add error logging
edits.append(("#2 GCS button URL",
"""function avGCS() {
  fetch('/api/gcs', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({intensity: 0.9})})
    .then(r=>r.json()).then(d=>console.log('GCS level:', d.level));
}""",
"""function avGCS() {
  var _b = (typeof API !== 'undefined' && API) ? API : '';
  var _h = {'Content-Type':'application/json'};
  try { if (typeof CONFIG !== 'undefined' && CONFIG.secret) _h['X-Vintos-Secret'] = CONFIG.secret; } catch(e){}
  fetch(_b + '/api/gcs', {method:'POST', headers:_h, body: JSON.stringify({intensity: 0.9})})
    .then(r=>r.json()).then(d=>console.log('GCS level:', d.level))
    .catch(e=>console.log('GCS error:', e));
}"""))

# #6 flicker — forward the live color into the glow target
edits.append(("#6 flicker carries color",
"""function _avApplyColor(hex) {
  _avStateColor = hex;""",
"""function _avApplyColor(hex) {
  _avStateColor = hex;
  try { if (typeof _avTargetColor !== 'undefined' && _avTargetColor && _avTargetColor.set) _avTargetColor.set(hex); } catch(e){}"""))

# #1 keep-messages — helpers inserted before _avParseReply
edits.append(("#1 helpers",
"function _avParseReply(raw) {",
"""function _avEsc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function _avLoadChat(){ try{ var s=localStorage.getItem('av_chat_history'); if(s){ var a=JSON.parse(s); if(Array.isArray(a)) _avChatHistory=a; } }catch(e){} }
function _avPersistChat(){ try{ localStorage.setItem('av_chat_history', JSON.stringify(_avChatHistory.slice(-20))); }catch(e){} }
function _avRenderStrip(pending){
  try{
    var box=document.getElementById('av-chat-message'); if(!box) return;
    var items=_avChatHistory.slice(-6), html='';
    for(var i=0;i<items.length;i++){
      var m=items[i], t=(m.role==='assistant')?_avParseReply(m.content).text:m.content;
      if(!t) continue;
      html += (m.role==='user')
        ? '<div style="font-style:normal;font-family:JetBrains Mono,monospace;font-size:11px;color:rgba(201,107,60,0.7);margin:8px 0 2px;">'+_avEsc(t)+'</div>'
        : '<div style="margin:2px 0 10px;">'+_avEsc(t)+'</div>';
    }
    if(pending) html += '<div style="opacity:0.5;">"""+E+"""</div>';
    box.innerHTML=html; box.scrollTop=box.scrollHeight;
  }catch(e){}
}
function _avParseReply(raw) {"""))

# #1 render on open (load kept history the first time)
edits.append(("#1 render on open",
"""  requestAnimationFrame(() => { overlay.style.opacity = '1'; });
  if (!_avOpen) {""",
"""  requestAnimationFrame(() => { overlay.style.opacity = '1'; });
  try { if(!_avChatHistory.length) _avLoadChat(); _avRenderStrip(false); } catch(e){}
  if (!_avOpen) {"""))

# #1 send flow: persist + render instead of single-line replace
edits.append(("#1 on send",
"""  _avChatHistory.push({role:'user', content:text});
  document.getElementById('av-chat-message').textContent='"""+E+"""';""",
"""  _avChatHistory.push({role:'user', content:text});
  _avPersistChat(); _avRenderStrip(true);"""))

edits.append(("#1 on reply",
"""    _avChatHistory.push({role:'assistant', content:raw});
    const {text:display, gestures, holds, spawns, color} = _avParseReply(raw);
    document.getElementById('av-chat-message').textContent = display;""",
"""    _avChatHistory.push({role:'assistant', content:raw});
    const {text:display, gestures, holds, spawns, color} = _avParseReply(raw);
    _avPersistChat(); _avRenderStrip(false);"""))

edits.append(("#1 on error",
"""  } catch(e) { document.getElementById('av-chat-message').textContent=''; }""",
"""  } catch(e) { _avRenderStrip(false); }"""))

# apply, fail-safe
failed = []
for label, old, new in edits:
    n = src.count(old)
    if n != 1:
        failed.append((label, n))
        continue
    src = src.replace(old, new, 1)

if failed:
    print("\n!! ABORTED — nothing written. These anchors did not match exactly once (Mac file differs):")
    for label, n in failed:
        print("   - %s : found %d times (need 1)" % (label, n))
    print("   Send me the current text of those spots and I'll re-anchor. His file is untouched.")
    sys.exit(2)

bak = path + ".bak-appbatch"
open(bak, "w", encoding="utf-8").write(orig)
open(path, "w", encoding="utf-8").write(src)

print("\n=== DIFF (review before building) ===")
diff = difflib.unified_diff(orig.splitlines(), src.splitlines(),
                            fromfile="index.html (before)", tofile="index.html (after)", lineterm="", n=1)
for l in diff:
    print(l)

print("\nbackup:", bak)
print("\nAll 7 anchors applied (GCS, flicker, + 5 keep-message hooks).")
print("To build:  cd vintos-app && npx cap sync ios && npx cap open ios   (then Run in Xcode)")
print("To revert: mv '%s' '%s'" % (bak, path))
