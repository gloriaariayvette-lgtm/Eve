#!/usr/bin/env python3
"""recon_emote_disappear.py — Mac, READ-ONLY. Diagnose 'avatar disappears for the duration of the emote.'
Dump the clip-remap + gesture-play path verbatim so we can see: (a) how track names are remapped,
(b) whether POSITION tracks (Mixamo hip translation, ~cm scale) are stripped or applied, (c) the avatar's
scale, (d) how clipAction is started/stopped. No writes."""
import os, re, glob
CANDS = [os.path.join(os.getcwd(), "src/index.html"), os.path.join(os.getcwd(), "index.html")]
CANDS += glob.glob(os.path.expanduser("~/**/vintos-app/src/index.html"), recursive=True)
IDX = next((p for p in CANDS if os.path.isfile(p)), None)
if not IDX:
    raise SystemExit("index.html not found — cwd=%s ; run from inside vintos-app" % os.getcwd())
print("[file]", IDX.replace(os.path.expanduser("~"), "~"))
L = open(IDX, encoding="utf-8", errors="ignore").read().split("\n")

def dump(pat, label, ctx=6, cap=6):
    print(f"\n===== {label} =====")
    n = 0
    for i, l in enumerate(L):
        if re.search(pat, l) and l.strip():
            lo, hi = max(0, i-ctx), min(len(L), i+ctx+1)
            for j in range(lo, hi):
                print(f"  {'>>' if j==i else '  '}{j+1:5}| {L[j].rstrip()[:120]}")
            print("  " + "-"*40)
            n += 1
            if n >= cap: break
    if n == 0: print("  (no match)")

dump(r'_avRemapClip|RemapClip', "remap function", ctx=14, cap=1)
dump(r'\.position|PositionKeyframe|VectorKeyframe|track\.name|\.tracks', "position-track handling in remap", ctx=2, cap=8)
dump(r'clipAction|mixer\.|fadeIn|\.play\(\)|\.stop\(\)|crossFade', "clip play / mixer", ctx=3, cap=8)
dump(r'FBXLoader|avatar-models/mixamo|loadGesture|_avPlayGesture|playGesture', "gesture load + play entry", ctx=6, cap=4)
dump(r'\.scale\.set|\.scale\.setScalar|model\.scale|avatar\.scale|\.scale =', "avatar scale", ctx=1, cap=8)
dump(r'\.visible\s*=|traverse.*visible|remove\(|scene\.add', "visibility / add-remove toggles", ctx=2, cap=8)
print("\n(done)")
