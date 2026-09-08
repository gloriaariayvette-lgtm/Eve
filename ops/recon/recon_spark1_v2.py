#!/usr/bin/env python3
"""recon_spark1_v2.py — Aegis, READ-ONLY, no LLM. Re-count value-map ranks correctly (prior regex missed
most). Show ONE full recent daily entry verbatim + count ranks by several patterns."""
import os, re
HOME = os.path.expanduser("~")
vm = os.path.join(HOME, ".openclaw/workspace/memory/value-map.md")
txt = open(vm, encoding="utf-8", errors="ignore").read()
entries = [e for e in re.split(r'(?m)^(?=## .*Value Map)', txt) if e.strip()]
print(f"daily entries: {len(entries)}")
# count via several markers
for pat, lbl in [(r'(?mi)^RANK\s*\d+', 'RANK N'), (r'(?mi)^\s*\d+[.)]\s', 'N. / N)'),
                 (r'(?mi)^\s*Why', 'Why:'), (r'(?mi)^\s*Evidence', 'Evidence:'),
                 (r'(?mi)^#{1,4}\s*\d+', '#N heading'), (r'\*\*', 'bold **')]:
    print(f"  {lbl:12} {len(re.findall(pat, txt))}")
print("\n=== last full daily entry ===")
print(re.sub(r'\n{3,}', '\n\n', entries[-1].strip())[:1400])
