#!/usr/bin/env python3
"""recon_triage_prompt.py — Aegis, READ-ONLY. Dump thread-triage.py lines 198..262 verbatim (the
introspective rating prompt + the parse + the write onto the thread), so temperature + stability can be
added to the SAME pass on exact anchors. Also show the llm() system prompt around line 44."""
import os
HOME = os.path.expanduser("~")
TT = os.path.join(HOME, ".vintos/workspace/scripts/thread-triage.py")
lines = open(TT, encoding="utf-8", errors="ignore").read().split("\n")
print("=== llm() helper (44..64) ===")
for i in range(43, min(64, len(lines))):
    print(f"{i+1:4}| {lines[i]}")
print("\n=== rating prompt + parse + write (198..262) — VERBATIM ===")
for i in range(197, min(262, len(lines))):
    print(f"{i+1:4}| {lines[i]}")
