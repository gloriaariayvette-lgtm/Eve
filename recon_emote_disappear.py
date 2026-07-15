#!/usr/bin/env python3
"""recon_emote_disappear.py — Mac, READ-ONLY. Diagnose 'avatar disappears for the duration of the emote.'
Dump the clip-remap + gesture-play path verbatim so we can see: (a) how track names are remapped,
(b) whether POSITION tracks (Mixamo hip translation, ~cm scale) are stripped or applied, (c) the avatar's
scale, (d) how clipAction is started/stopped. No writes."""
import os, re
CWD = os.getcwd()
CANDS = [os.path.join(CWD, sub, "index.html") for sub in
         ("src", "www", "dist", "public", "app", "build", ".")]
IDX = next((p for p in CANDS if os.path.isfile(p)), None)
if not IDX:
    # bounded, non-recursive-ish walk (depth<=3), pruning heavy dirs — find the biggest index.html
    SKIP = {"node_modules", "Pods", "build", ".git", "DerivedData", "ios", "android"}
    hits = []
    base_depth = CWD.rstrip("/").count("/")
    for root, dirs, files in os.walk(CWD):
        if root.count("/") - base_depth > 3:
            dirs[:] = []; continue
        dirs[:] = [d for d in dirs if d not in SKIP]
        if "index.html" in files:
            p = os.path.join(root, "index.html")
            hits.append((os.path.getsize(p), p))
    if hits:
        hits.sort(reverse=True)
        print("[candidates found]")
        for sz, p in hits[:8]:
            print(f"   {sz:>9}B  {p.replace(os.path.expanduser('~'),'~')}")
        IDX = hits[0][1]
if not IDX:
    print("[cwd listing]", CWD)
    for e in sorted(os.listdir(CWD))[:40]:
        print("   ", e)
    raise SystemExit("no index.html found under cwd (depth<=3) — paste the listing above")
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
