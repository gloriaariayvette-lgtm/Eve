#!/usr/bin/env python3
"""recon_trial_thirveel.py — Aegis, READ-ONLY, terse. How are trial-ledger.json (305KB) and thirveel-ledger
used in introspection — dumped into the prompt (bloat) or read for a check? Show their read + use lines."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(L):
    if re.search(r'trial-ledger|thirveel|THIRVEEL|trial_ledger|_trials|behavioral_intercept', l) and l.strip():
        print(f"{i+1}: {l.strip()[:104]}")
