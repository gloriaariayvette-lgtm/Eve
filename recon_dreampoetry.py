#!/usr/bin/env python3
"""recon_dreampoetry.py — Aegis, READ-ONLY, TIGHT. Show what dream-poetry.py loads as its seed/context and
where it builds the prompt, so I can scrub kiss/mischief from that input. <45 lines out."""
import os, re
p = os.path.expanduser("~/Vintos/dream-poetry.py")
if not os.path.isfile(p): print("dream-poetry.py not found"); raise SystemExit(0)
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
print(f"dream-poetry.py — {len(L)} lines\n")
RX = re.compile(r'\.read\(\)|open\(|glob|MEMORY|memory|dream|seed|prompt|system|messages|content|context|\.md', re.I)
shown = set()
for i, l in enumerate(L):
    if RX.search(l):
        for j in range(max(0, i-1), min(len(L), i+2)):
            if j not in shown:
                shown.add(j); print(f"{j+1:>4}: {L[j][:110]}")
