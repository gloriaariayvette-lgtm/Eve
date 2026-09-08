#!/usr/bin/env python3
"""recon_intro_threads.py — Aegis, READ-ONLY, terse. Every t1/t2/Thread/.start() reference in introspection,
to find where the first-pass threads are created (or confirm they're missing)."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(L):
    if re.search(r'\bt1\b|\bt2\b|threading\.Thread|Thread\(|\.start\(\)', l) and l.strip():
        print(f"{i+1}: {l.strip()[:104]}")
