#!/usr/bin/env python3
"""recon_constraints.py — Aegis, READ-ONLY, terse. Find where system_msg is built and the constraint/rule
sentences (word-bans, do-not-repeat, formatting) so we can strip them for the a1/b1 reasoning prompt only."""
import os, re
HOME = os.path.expanduser("~")
JP = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
L = open(JP, encoding="utf-8", errors="ignore").read().split("\n")
print("-- system_msg assembly --")
for i, l in enumerate(L):
    if re.search(r'\bsystem_msg\s*=|\bsystem_msg\s*\+=|user_msg\s*=', l) and l.strip():
        print(f"{i+1}: {l.strip()[:90]}")
print("-- constraint/rule lines --")
n = 0
for i, l in enumerate(L):
    if re.search(r"do not|don't|avoid|never |No ['\"]|banned|forbidden|do not repeat|do not begin|must reference|must name", l, re.I) and l.strip() and not l.strip().startswith("#"):
        print(f"{i+1}: {l.strip()[:88]}")
        n += 1
        if n >= 16: break
