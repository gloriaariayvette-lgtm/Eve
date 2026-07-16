#!/usr/bin/env python3
"""recon_intro_find.py — Aegis, READ-ONLY. Locate `d = json.load(open(path))` in introspection.sh and show the
lines above it with running bracket balance, to pinpoint the unclosed (/[/{ that makes Python think a comma is
missing. repr() reveals hidden chars."""
import os
P = os.path.expanduser("~/Vintos/introspection.sh")
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
hits = [i for i, l in enumerate(lines) if "json.load(open(path))" in l or "d = json.load" in l]
print(f"matches for 'd = json.load(open(path))': {[h+1 for h in hits]}\n")
for h in hits[:3]:
    lo = max(0, h-24)
    print(f"===== around L{h+1} (running bracket balance) =====")
    bal = 0
    seg = []
    for n in range(lo, min(len(lines), h+3)):
        l = lines[n]
        # crude balance ignoring strings/comments (good enough to spot a gross imbalance)
        for ch in l:
            if ch in "([{": bal += 1
            elif ch in ")]}": bal -= 1
        tag = ">>" if n == h else "  "
        print(f"{tag} {n+1} [bal {bal:+d}]: {l[:100]}")
    print()
