#!/usr/bin/env python3
"""show_agedays.py — Aegis, READ-ONLY. emoclaw_utils lines 888-948 (the age_days / expiry region) verbatim."""
import os
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/emoclaw_utils.py")
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")
# find the enclosing def
start = 888
for i in range(900, 860, -1):
    if L[i].lstrip().startswith("def "):
        start = i; break
for i in range(start, min(len(L), 950)):
    if L[i].rstrip(): print(f"{i+1}: {L[i].rstrip()[:112]}")
