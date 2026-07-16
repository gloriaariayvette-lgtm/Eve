#!/usr/bin/env python3
"""show_sections.py — Aegis, READ-ONLY, terse. Biggest sections in the current (capped) introspection prompt."""
import os, re
f = "/tmp/velaris_intro_prompt.txt"
txt = open(f, encoding="utf-8", errors="ignore").read()
print(f"total: {len(txt):,}B (~{len(txt)//4:,} tok)")
chunks = re.split(r'\n(?=[A-Z][A-Z ]{4,}[:=]|\#\#|\=\=\=|---|\[[A-Z])', txt)
for c in sorted(chunks, key=len, reverse=True)[:10]:
    print(f"  {len(c):>8,}B  {re.sub(chr(10),' ',c[:70])}")
