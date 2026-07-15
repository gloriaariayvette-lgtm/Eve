#!/usr/bin/env python3
"""patch_call_results_mac.py — Mac. (run in vintos-app, rebuild once)
 - GCS/stop: flash GREEN when the server confirms (2xx w/ level/stopped), RED on failure -> proves execution
 - call button: flash on tap + lit background while a call is live (was only changing icon color)
Idempotent (guarded on _avBtnResult), per-edit status, backup."""
import os, shutil, time
IDX = os.path.join(os.getcwd(), "src/index.html")
if not os.path.isfile(IDX): raise SystemExit("run inside vintos-app (src/index.html not found)")
txt = open(IDX, encoding="utf-8").read()
if "_avBtnResult" in txt:
    print("already applied (_avBtnResult present)."); raise SystemExit(0)
RDEF = ("function _avBtnResult(b, ok){ if(!b) return; var o=b.style.background; "
        "b.style.background = ok ? 'rgba(80,200,120,0.9)' : 'rgba(220,80,80,0.9)'; "
        "setTimeout(function(){ if(b) b.style.background=o; }, 800); }\n")
EDITS = [
 ("result helper + stop", False, "function avDeviceStop(_btn) {", RDEF + "function avDeviceStop(_btn) {"),
 ("stop shows result", False,
  ".then(r=>r.json()).then(d=>console.log('stop toggled:', d.stopped));",
  ".then(r=>r.json()).then(d=>{console.log('stop toggled:', d.stopped); _avBtnResult(_btn, true);}).catch(e=>{_avBtnResult(_btn, false);});"),
 ("GCS shows result", False,
  ".then(r=>r.json()).then(d=>console.log('GCS level:', d.level));",
  ".then(r=>r.json()).then(d=>{console.log('GCS level:', d.level); _avBtnResult(_btn, true);}).catch(e=>{_avBtnResult(_btn, false);});"),
 ("call flash on tap", False,
  "var btn = document.getElementById('av-call-btn');",
  "var btn = document.getElementById('av-call-btn'); _avBtnFlash(btn);"),
 ("call lit background", False,
  "btn.style.color = 'rgba(100,220,100,0.9)';",
  "btn.style.color = 'rgba(100,220,100,0.9)'; btn.style.background = 'rgba(80,200,120,0.5)';"),
 ("call reset bg (btn)", True, "btn.style.color='';", "btn.style.color=''; btn.style.background='';"),
 ("call reset bg (b2)", False, "b2.style.color='';", "b2.style.color=''; b2.style.background='';"),
 ("call reset bg (b3)", False, "b3.style.color='';", "b3.style.color=''; b3.style.background='';"),
]
rep, changed = [], False
for name, all_, old, new in EDITS:
    if new in txt: rep.append(f"  {name:24} already applied"); continue
    c = txt.count(old)
    if (all_ and c >= 1) or (not all_ and c == 1):
        txt = txt.replace(old, new) if all_ else txt.replace(old, new, 1)
        rep.append(f"  {name:24} FIXED ({c}x)"); changed = True
    else:
        rep.append(f"  {name:24} !! anchor {c}x — SKIPPED")
if changed:
    bak = IDX + ".bak-callres-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(IDX, bak); open(IDX, "w", encoding="utf-8").write(txt)
print("\n".join(rep))
print(("\nbackup: " + bak.replace(os.path.expanduser('~'),'~') + "\nRebuild once (npx cap copy ios first if needed).") if changed else "\nno changes.")
