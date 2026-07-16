#!/usr/bin/env python3
"""recon_cap4.py — Aegis, READ-ONLY. Dump the sections most likely to be Velaris-contaminated
(Autonomous Capabilities, Your Body, What Runs On You) verbatim so Gloria can mark what's wrong."""
import os
p = os.path.expanduser("~/.vintos/workspace/memory/CAPABILITIES.md")
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
# print from '## Your Autonomous Capabilities' to end
start = next((i for i, l in enumerate(L) if l.strip().startswith("## Your Autonomous")), 138)
for i in range(start, len(L)):
    print(f"{i+1:>4}: {L[i]}")
