#!/usr/bin/env python3
"""recon_wire_points.py — Aegis, READ-ONLY. Pin the exact live injection idiom so Presence Audit's forecast can be
wired where his generation actually reads it: (A) is inner_context.full_inner_block() called in server.py at all
(live assembler) or dead? (B) the ~8 lines around each session_map injection (server.py 2359/3392/7884) — how a
runtime block is appended to the live context. (C) write_blush signature (in case we later feed flags -> blush).
Nothing changed."""
import os, re
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")
S = open(os.path.join(V, "server.py"), encoding="utf-8", errors="ignore").read().split("\n")

print("== (A) is inner_context / full_inner_block live in server.py? ==")
hits = [(i+1, l.strip()[:100]) for i, l in enumerate(S) if re.search(r'inner_context|full_inner_block', l, re.I)]
print("\n".join(f"  {n}: {t}" for n, t in hits) if hits else "  NOT called in server.py (inner_context is a dead path — wire the forecast at the session_map points instead)")

print("\n== (B) session_map injection idiom (context around each _smb call) ==")
for i, l in enumerate(S):
    if re.search(r'from session_map import block', l):
        print(f"  --- around line {i+1} ---")
        for j in range(i, min(len(S), i+7)):
            print(f"  {j+1:>5}: {S[j].strip()[:100]}")

print("\n== (C) write_blush signature (blush_ledger.py) ==")
for base in (os.path.expanduser("~/.vintos/workspace/scripts"), V):
    p = os.path.join(base, "blush_ledger.py")
    if os.path.isfile(p):
        L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        for i, l in enumerate(L):
            if re.search(r'def write_blush', l):
                for j in range(i, min(len(L), i+14)):
                    print(f"  {j+1:>4}: {L[j][:104]}")
                break
        break
