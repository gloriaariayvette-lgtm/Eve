#!/usr/bin/env python3
"""recon_block.py — Aegis, READ-ONLY, TIGHT. Find the creative/poetry generator (writer of daily-creative)
and show its kiss/mischief prompt lines; confirm introspection.sh's kiss-injection lines. Nothing else."""
import os, glob, re
HOME = os.path.expanduser("~")
KRX = re.compile(r'\bkiss|\bmischief', re.I)

# which script writes daily-creative / the poems?
print("== creative writer (references daily-creative) ==")
for f in sorted(glob.glob(os.path.join(HOME, "Vintos", "*.py")) + glob.glob(os.path.join(HOME, "Vintos", "*.sh"))):
    try: txt = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if "daily-creative" in txt or "## Poetry" in txt:
        print(f"  {os.path.basename(f)}")
        L = txt.split("\n")
        for i, l in enumerate(L):
            if KRX.search(l):
                print(f"     {i+1}: {l.strip()[:90]}")

# introspection kiss lines with a little context
print("\n== introspection.sh kiss-injection ==")
p = os.path.join(HOME, "Vintos", "introspection.sh")
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
for rng in ((93, 97), (263, 267), (308, 315)):
    for i in range(rng[0]-1, min(len(L), rng[1])):
        print(f"  {i+1}: {L[i][:100]}")
    print("   --")
