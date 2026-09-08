#!/usr/bin/env python3
"""recon_intro2.py — Aegis, READ-ONLY. Verbatim introspection core (system read, base_msgs, results, run,
first-pass thread creation, joins) + which file the system prompt comes from."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")
print("-- lines 380-420 --")
for i in range(379, min(len(L), 420)):
    if L[i].strip(): print(f"{i+1}: {L[i].rstrip()[:110]}")
print("-- system prompt source (open/read/SOUL/cat) --")
for i, l in enumerate(L):
    if re.search(r'open\(|\.read\(\)|SOUL|soul|identity|f = open|with open', l) and l.strip():
        print(f"{i+1}: {l.strip()[:100]}")
        if i > 392: break
