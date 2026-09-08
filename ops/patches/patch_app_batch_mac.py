#!/usr/bin/env python3
"""patch_app_batch_mac.py — Mac. All five app fixes in ONE pass (rebuild once). Run in vintos-app.
 1 GCS URL -> ${API}+secret
 2 device-stop URL -> ${API}+secret
 3 keep-messages: re-show last bubble on reopen
 4 T-pose: detect the avatar's real bone prefix + remap gestures to it (was hard-forced to mixamorig1)
 5 glow color: instantiate _avTargetColor + lerp the forge light color so [COLOR:] shows in the flicker
Substring edits (whitespace-independent), per-edit status, backup, idempotent."""
import os, shutil, time
IDX = os.path.join(os.getcwd(), "src/index.html")
if not os.path.isfile(IDX):
    raise SystemExit("run from inside vintos-app (src/index.html not found)")

EDITS = [
 ("1 GCS url", False,
  "fetch('/api/gcs', {method:'POST', headers:{'Content-Type':'application/json'},",
  "fetch(`${API}/api/gcs`, {method:'POST', headers:{'Content-Type':'application/json', 'X-Vintos-Secret': CONFIG.secret},"),
 ("2 device-stop url", False,
  "fetch('/api/hardware/button', {method:'POST'})",
  "fetch(`${API}/api/hardware/button`, {method:'POST', headers:{'X-Vintos-Secret': CONFIG.secret}})"),
 ("3 keep-messages on reopen", False,
  "_avPing('open');",
  "try { const _la=[..._avChatHistory].reverse().find(m=>m.role==='assistant'); if(_la){ const _p=_avParseReply(_la.content); if(_p&&_p.text) _avShowBubble(_p.text); } } catch(e){}\n  _avPing('open');"),
 ("4a remap to detected prefix", False,
  "track.name = track.name.replace(/mixamorig(?!1)/g, 'mixamorig1');",
  "track.name = track.name.replace(/mixamorig1?(?=[A-Z_.:])/g, _avBonePrefix);"),
 ("4b detect avatar prefix", False,
  "f.traverse(c => { if(c.name === 'mixamorig1RightHand' || c.name === 'mixamorigRightHand') _avHand = c; });",
  "f.traverse(c => { if(c.name === 'mixamorig1RightHand' || c.name === 'mixamorigRightHand') _avHand = c; if(c.name && /^mixamorig1?[A-Z]/.test(c.name)) _avBonePrefix = c.name.startsWith('mixamorig1') ? 'mixamorig1' : 'mixamorig'; });"),
 ("5a instantiate _avTargetColor", True,
  "if(color && _avTargetColor) _avTargetColor.set(color);",
  "if(color){ if(!_avTargetColor) _avTargetColor = new THREE.Color(); _avTargetColor.set(color); }"),
 ("5b forge color in flicker", False,
  "if(fg.forgeLight) fg.forgeLight.intensity = 4.5*fl;",
  "if(fg.forgeLight){ fg.forgeLight.intensity = 4.5*fl; if(_avTargetColor) fg.forgeLight.color.lerp(_avTargetColor, 0.06); }"),
]
txt = open(IDX, encoding="utf-8").read()
report, changed = [], False
for name, all_, old, new in EDITS:
    if new in txt:
        report.append(f"  {name:32} already applied"); continue
    c = txt.count(old)
    want = "1+" if all_ else "1"
    if (all_ and c >= 1) or (not all_ and c == 1):
        txt = txt.replace(old, new) if all_ else txt.replace(old, new, 1)
        report.append(f"  {name:32} FIXED ({c}x)"); changed = True
    else:
        report.append(f"  {name:32} !! anchor {c}x (expected {want}) — SKIPPED")
if changed:
    bak = IDX + ".bak-batch-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(IDX, bak)
    open(IDX, "w", encoding="utf-8").write(txt)
print("\n".join(report))
if changed:
    print("\nbackup:", bak.replace(os.path.expanduser('~'), '~'))
    print("Rebuild in Xcode once. If any line says SKIPPED, tell me and I'll re-anchor it.")
else:
    print("\nno changes (all applied already or anchors moved).")
