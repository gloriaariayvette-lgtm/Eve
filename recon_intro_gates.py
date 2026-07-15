#!/usr/bin/env python3
"""recon_intro_gates.py — Aegis, READ-ONLY, terse. Early-exit gates in introspection.sh bash portion
(before the python heredoc at ~382) so we can bypass them for a sandboxed test."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")
for i in range(0, min(len(L), 382)):
    l = L[i]
    if re.search(r'\bexit\b|\breturn\b|lock|flock|already|cooldown|idle|HOUR|last.?run|-lt|-ge|consent|sleep', l) and l.strip() and not l.strip().startswith("#"):
        print(f"{i+1}: {l.strip()[:100]}")
