#!/usr/bin/env python3
"""verify_and_recon_buttons.py — Mac, READ-ONLY. (A) Is the patch actually in src/index.html? Check each
of the 5 fix markers. (B) Recon the mic/voice button (why no green) + the GCS/stop/call button row so I can
add visible click feedback. Run in vintos-app."""
import os, re
IDX = os.path.join(os.getcwd(), "src/index.html")
txt = open(IDX, encoding="utf-8", errors="ignore").read()
L = txt.split("\n")
print("=== (A) are the 5 fixes present in src/index.html? ===")
checks = {
 "1 GCS ${API}":        "`${API}/api/gcs`",
 "2 stop ${API}":       "`${API}/api/hardware/button`",
 "3 keep-messages":     "reverse().find(m=>m.role==='assistant')",
 "4a remap prefix":     "/mixamorig1?(?=[A-Z_.:])/g",
 "4b detect prefix":    "_avBonePrefix = c.name.startsWith('mixamorig1')",
 "5a target color":     "if(!_avTargetColor) _avTargetColor = new THREE.Color()",
 "5b forge color lerp": "fg.forgeLight.color.lerp(_avTargetColor",
}
for name, mark in checks.items():
    print(f"  {name:22} {'PRESENT ✓' if mark in txt else 'MISSING ✗ (patch not in file / stale)'}")

print("\n=== (B) mic / voice button (why not green) ===")
n = 0
for i, l in enumerate(L):
    if re.search(r'mic|micButton|av-mic|voice.*btn|record|isRecording|listening|MediaRecorder|getUserMedia|green', l, re.I) and l.strip():
        print(f"  {i+1}| {l.strip()[:112]}"); n += 1
        if n >= 18: break

print("\n=== (B) the GCS/stop/call button row (current visual state / feedback) ===")
n = 0
for i, l in enumerate(L):
    if re.search(r'avGCS|avDeviceStop|avCall|onclick="av|right-side buttons|\.active|:active|classList', l) and l.strip():
        print(f"  {i+1}| {l.strip()[:112]}"); n += 1
        if n >= 16: break
