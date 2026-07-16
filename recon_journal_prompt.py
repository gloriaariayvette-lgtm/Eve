#!/usr/bin/env python3
"""recon_journal_prompt.py — Aegis, READ-ONLY, terse. Find the journal's writing-instruction / STRUCTURE
block + where 'what you made' (DISCOVERIES/daily-creative) is referenced, so we add the 'what I made today /
what I want to do next' forward-progress framing in the right spot."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(L):
    if re.search(r'STRUCTURE|three zones|_concrete_header|YOUR SOURCES|DAILY CREATIVE|what you made|what comes to mind|_topic_prefix|write what|next|forward|USER_PROMPT|system_msg\s*=', l) and l.strip():
        print(f"{i+1}: {l.strip()[:100]}")
