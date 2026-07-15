#!/usr/bin/env python3
"""find_gloria_routed.py — Aegis, READ-ONLY, terse. Find the gloria_routed -> auto-fulfill-after-3-days logic
in the want system (and whether it's reachable / broken)."""
import os, re, glob
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
for f in sorted(glob.glob(os.path.join(SC, "*want*")) + [os.path.join(SC, "emoclaw_utils.py")]):
    if not os.path.isfile(f): continue
    L = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    hits = [i for i, l in enumerate(L) if re.search(r'gloria_routed|routed.*gloria|3\s*day|72\s*hour|259200|3\s*\*\s*86400|days\s*[>=]\s*3|>=?\s*3\b.*day', l, re.I) and l.strip()]
    if not hits: continue
    print(f"== {os.path.basename(f)} ==")
    shown = set()
    for i in hits:
        for j in range(max(0, i-1), min(len(L), i+3)):
            if j in shown or not L[j].strip(): continue
            shown.add(j); print(f"{j+1}: {L[j].strip()[:100]}")
        if len(shown) > 30: break
