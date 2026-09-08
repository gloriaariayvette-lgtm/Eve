#!/usr/bin/env python3
"""show_autostale.py — Aegis, READ-ONLY. wants-router.py lines 1778-1826 verbatim: the gloria_routed
auto-fulfill-after-3-days block, to find why it isn't firing."""
import os
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/wants-router.py")
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")
for i in range(1777, min(len(L), 1826)):
    print(f"{i+1}: {L[i].rstrip()[:118]}")
