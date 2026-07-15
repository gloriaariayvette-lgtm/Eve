#!/usr/bin/env python3
"""recon_app_touch.py — Mac, READ-ONLY. Show the touch system: the overlay tap handler (ex/ey -> body
region), the touch-point/zone definitions (to add 'chest'), and how a touch fires the speech bubble."""
import os, re
IDX = os.path.join(os.getcwd(), "src/index.html")
L = open(IDX, encoding="utf-8", errors="ignore").read().split("\n")
# full tap handler
start = next((i for i,l in enumerate(L) if re.search(r"addEventListener\('(click|pointerdown|touchstart)'|_avOnTap|function _avTap|overlay.*addEventListener", l)), None)
if start is None:
    start = next((i for i,l in enumerate(L) if "const ex = e.clientX" in l), 3130) - 6
print(f"=== tap handler (from {start+1}) ===")
for j in range(start, min(start+70, len(L))):
    if L[j].strip(): print(f"  {j+1}| {L[j].strip()[:118]}")
print("\n=== touch-point / body-region zones (where to add chest) ===")
n=0
for i,l in enumerate(L):
    if re.search(r'head|chest|hand|face|belly|hip|thigh|region|zone|touchPoint|bodyPart|_avZones|hitTest|part:', l, re.I) and re.search(r'0\.\d|x:|y:|region|zone|part|touch', l) and l.strip():
        print(f"  {i+1}| {l.strip()[:112]}"); n+=1
        if n>=18: break
print("\n=== how a touch fires the bubble / response ===")
n=0
for i,l in enumerate(L):
    if re.search(r'/api/avatar/touch|_avSpeakAndShow|_avShowBubble|touch.*fetch|onTouch|api/touch', l) and l.strip():
        print(f"  {i+1}| {l.strip()[:112]}"); n+=1
        if n>=12: break
