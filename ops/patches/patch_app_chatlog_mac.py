#!/usr/bin/env python3
"""patch_app_chatlog_mac.py — Mac. Three fixes, one rebuild (run in vintos-app):
 A) running chat log: av-chat-message becomes a scrollback of BOTH sides, persists, repopulates on reopen
 B) speech bubble back to touch-only: undo my stray _avShowBubble-on-open (reopen now renders the log)
 C) chest touch point: new zone between face and feet -> _avTouchResponse('chest')
Per-edit status, backup, idempotent."""
import os, shutil, time
IDX = os.path.join(os.getcwd(), "src/index.html")
if not os.path.isfile(IDX): raise SystemExit("run inside vintos-app (src/index.html not found)")

HELPERS = (
"function _avLogMsg(role, text){\n"
"  var box = document.getElementById('av-chat-message');\n"
"  if(!box || !text) return;\n"
"  box.style.maxHeight='110px'; box.style.overflowY='auto'; box.style.textAlign='left';\n"
"  var isU = role==='user', isSys = role==='system';\n"
"  var line = document.createElement('div');\n"
"  line.style.cssText = 'margin:3px 0;line-height:1.4;'+(isU?'color:rgba(201,107,60,0.95);':(isSys?'color:var(--text-dim,#7d766b);font-size:11px;opacity:0.7;':'color:var(--text-bright,#EDE7DC);'));\n"
"  line.textContent = (isU?'You: ':'')+text;\n"
"  box.appendChild(line);\n"
"  while(box.children.length>14) box.removeChild(box.firstChild);\n"
"  box.scrollTop = box.scrollHeight;\n"
"}\n"
"function _avRenderChatLog(){\n"
"  var box = document.getElementById('av-chat-message');\n"
"  if(!box) return;\n"
"  box.innerHTML='';\n"
"  var h = _avChatHistory.slice(-14);\n"
"  for(var i=0;i<h.length;i++){\n"
"    var m = h[i], disp = m.content;\n"
"    var rl = (m.role==='user' && String(m.content).charAt(0)==='[') ? 'system' : m.role;\n"
"    if(m.role==='assistant'){ try{ disp=_avParseReply(m.content).text||m.content; }catch(e){} }\n"
"    if(disp) _avLogMsg(rl, disp);\n"
"  }\n"
"}\n"
"async function _avSpeakAndShow(raw, eventNote) {")

CHEST = ("  // Chest zone — below the face, upper-mid torso, center\n"
         "  if(ey >= H*0.38 && ey < H*0.58 && ex > W*0.30 && ex < W*0.70) {\n"
         "    _avTouchResponse('chest');\n"
         "    return;\n"
         "  }\n"
         "  // Feet zone — lower portion above chat strip")

EDITS = [
 ("A helpers", False, "async function _avSpeakAndShow(raw, eventNote) {", HELPERS),
 ("A user->log", False, "_avChatHistory.push({role:'user', content:text});", "_avChatHistory.push({role:'user', content:text}); _avLogMsg('user', text);"),
 ("A drop pending", False, "document.getElementById('av-chat-message').textContent='…';", ""),
 ("A assistant->log", False, "document.getElementById('av-chat-message').textContent = display;", "_avLogMsg('assistant', display);"),
 ("A touch->log", False, "  _avShowBubble(display);\n  _avCheckCommandBubble();",
   "  _avShowBubble(display);\n  if(eventNote) _avLogMsg('system', eventNote); _avLogMsg('assistant', display);\n  _avCheckCommandBubble();"),
 ("B reopen->log", False,
   "const _la=[..._avChatHistory].reverse().find(m=>m.role==='assistant'); if(_la){ const _p=_avParseReply(_la.content); if(_p&&_p.text) _avShowBubble(_p.text); }",
   "_avRenderChatLog();"),
 ("C chest zone", False, "  // Feet zone — lower portion above chat strip", CHEST),
]
txt = open(IDX, encoding="utf-8").read()
rep, changed = [], False
for name, all_, old, new in EDITS:
    if new and new in txt and name != "A drop pending": rep.append(f"  {name:20} already"); continue
    c = txt.count(old)
    if c == 1:
        txt = txt.replace(old, new, 1); rep.append(f"  {name:20} FIXED"); changed = True
    else:
        rep.append(f"  {name:20} !! anchor {c}x — SKIPPED")
if changed:
    bak = IDX + ".bak-chatlog-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(IDX, bak); open(IDX, "w", encoding="utf-8").write(txt)
print("\n".join(rep))
print(("\nbackup: " + bak.replace(os.path.expanduser('~'),'~') + "\nRebuild once (npx cap copy ios first if needed).") if changed else "\nno changes.")
