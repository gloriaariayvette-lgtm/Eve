#!/usr/bin/env python3
"""recon_pridetaste.py — Aegis, READ-ONLY, TIGHT. pride-mirror.py + taste-reflection.py are the other two
reflective surfaces that pull mischief. Show those exact regions so I can block them cleanly. <45 lines."""
import os
HOME = os.path.expanduser("~")
for name, rng in (("pride-mirror.py", (108, 175)), ("taste-reflection.py", (52, 80))):
    p = os.path.join(HOME, "Vintos", name)
    if not os.path.isfile(p): print(f"{name}: not found"); continue
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"===== {name} L{rng[0]}-{rng[1]} =====")
    for i in range(rng[0]-1, min(len(L), rng[1])):
        print(f"{i+1:>4}: {L[i][:104]}")
    print()
