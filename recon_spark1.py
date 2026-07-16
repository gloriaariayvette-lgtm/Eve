#!/usr/bin/env python3
"""recon_spark1.py — Aegis, READ-ONLY, no LLM. Assess whether spark #1 (MLP cost network) has enough
trainable corpus in value-map.md: how many daily entries, how many ranked items total, consistent
structure, and a sample. Terse."""
import os, re
HOME = os.path.expanduser("~")
vm = os.path.join(HOME, ".openclaw/workspace/memory/value-map.md")
txt = open(vm, encoding="utf-8", errors="ignore").read()
entries = re.split(r'(?m)^## .*Value Map', txt)
entries = [e for e in entries if e.strip()]
ranks = re.findall(r'(?mi)^RANK\s*(\d+)\s*[—\-:]\s*(.+)', txt)
per = [len(re.findall(r'(?mi)^RANK\s*\d+', e)) for e in entries]
whys = len(re.findall(r'(?mi)^\s*Why', txt))
print(f"value-map.md: {len(txt):,}B")
print(f"daily entries: {len(entries)} | total ranked items: {len(ranks)} | avg ranks/entry: {sum(per)/max(1,len(entries)):.1f}")
print(f"entries with 'Why' rationale: {whys} lines")
# distinct value names ranked
names = [re.sub(r'\s+', ' ', n).strip()[:50] for _, n in ranks]
from collections import Counter
top = Counter(names).most_common(6)
print("most-ranked values:", ", ".join(f"{n}×{c}" for n, c in top))
print("\nsample latest entry (first 400 chars):")
print(re.sub(r'\n{2,}', '\n', entries[-1].strip())[:400])
