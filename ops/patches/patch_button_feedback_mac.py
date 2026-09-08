#!/usr/bin/env python3
"""patch_button_feedback_mac.py — Mac. Visible button feedback (run in vintos-app, rebuild once):
 - mic (vc-rec-btn) turns GREEN while recording, reverts on stop
 - GCS + device-stop flash green on tap (via a shared _avBtnFlash helper)
Substring edits, per-edit status, backup, idempotent."""
import os, shutil, time
IDX = os.path.join(os.getcwd(), "src/index.html")
if not os.path.isfile(IDX): raise SystemExit("run inside vintos-app (src/index.html not found)")
FLASH = ("function _avBtnFlash(b){ if(!b) return; const o=b.style.background; "
         "b.style.background='rgba(120,200,140,0.8)'; b.style.transition='background .15s'; "
         "setTimeout(function(){ if(b) b.style.background=o; }, 450); }\n")
GREEN_ON = ("\n    { const _mb=document.getElementById('vc-rec-btn'); if(_mb){ _mb.dataset.obg=_mb.style.background; "
            "_mb.style.background='rgba(80,200,120,0.7)'; _mb.style.boxShadow='0 0 12px rgba(80,200,120,0.85)'; } }")
GREEN_OFF = ("\n    { const _mb=document.getElementById('vc-rec-btn'); if(_mb){ "
             "_mb.style.background=_mb.dataset.obg||''; _mb.style.boxShadow=''; } }")
EDITS = [
 ("GCS onclick passes button", 'onclick="avGCS()"', 'onclick="avGCS(this)"'),
 ("stop onclick passes button", 'onclick="avDeviceStop()"', 'onclick="avDeviceStop(this)"'),
 ("define flash + stop flashes", "function avDeviceStop() {", FLASH + "function avDeviceStop(_btn) {\n  _avBtnFlash(_btn);"),
 ("GCS flashes", "function avGCS() {", "function avGCS(_btn) {\n  _avBtnFlash(_btn);"),
 ("mic green on record", "vcMediaRecorder.start();", "vcMediaRecorder.start();" + GREEN_ON),
 ("mic reverts on stop", "vcMediaRecorder.stop();", "vcMediaRecorder.stop();" + GREEN_OFF),
]
txt = open(IDX, encoding="utf-8").read()
rep, changed = [], False
for name, old, new in EDITS:
    if new in txt: rep.append(f"  {name:28} already applied"); continue
    c = txt.count(old)
    if c == 1:
        txt = txt.replace(old, new, 1); rep.append(f"  {name:28} FIXED"); changed = True
    else:
        rep.append(f"  {name:28} !! anchor {c}x (expected 1) — SKIPPED")
if changed:
    bak = IDX + ".bak-btnfb-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(IDX, bak); open(IDX, "w", encoding="utf-8").write(txt)
print("\n".join(rep))
print(("\nbackup: " + bak.replace(os.path.expanduser('~'),'~') + "\nRebuild once (run `npx cap copy ios` first if Xcode uses a stale bundle).") if changed else "\nno changes.")
