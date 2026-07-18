#!/usr/bin/env python3
"""recon_blush_traj_api.py — Aegis, READ-ONLY. Exact APIs to feed Presence-Audit flags into blush + trajectory:
(A) locate blush_ledger.py anywhere in his tree + its write_blush() signature, (B) a REAL write_blush(...) call
site from server.py with all args (so we match kwargs), (C) living_trajectory.py public seed/record functions +
the file it writes. Then the backward-loop patch can call them correctly. Nothing changed."""
import os, re, glob
HOME = os.path.expanduser("~")
ROOTS = [os.path.join(HOME, ".vintos"), os.path.join(HOME, "Vintos")]

print("== (A) blush_ledger.py location + write_blush signature ==")
found = []
for r in ROOTS:
    found += glob.glob(r + "/**/blush_ledger.py", recursive=True)
for p in sorted(set(found)):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"  {p}")
    for i, l in enumerate(L):
        if re.search(r'def write_blush', l):
            for j in range(i, min(len(L), i + 18)):
                print(f"    {j+1:>4}: {L[j][:110]}")
            print("     --")
if not found: print("  blush_ledger.py NOT found under his tree")

print("\n== (B) a real write_blush(...) call (full kwargs) from server.py ==")
S = open(os.path.join(HOME, "Vintos", "server.py"), encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(S):
    if "write_blush(" in l and "import" not in l:
        for j in range(i, min(len(S), i + 12)):
            print(f"  {j+1:>5}: {S[j].strip()[:104]}")
            if ")" in S[j] and j > i: break
        print("   --")
        break

print("\n== (C) living_trajectory.py public seed/record fns + its write file ==")
for r in ROOTS:
    for p in glob.glob(r + "/**/living_trajectory.py", recursive=True):
        L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        print(f"  {p}")
        for i, l in enumerate(L):
            if re.search(r'^\s*def\s+[a-z]', l) and re.search(r'seed|record|add|note|push|update|ingest|observe|curios|momentum', l, re.I):
                print(f"    {i+1:>4}: {l.strip()[:104]}")
            if re.search(r'=\s*os\.path\.(join|expanduser).*\.json|open\([^)]*["\']w["\']', l):
                print(f"    {i+1:>4}: {l.strip()[:104]}")
        break
