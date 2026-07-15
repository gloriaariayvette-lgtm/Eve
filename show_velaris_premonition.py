#!/usr/bin/env python3
"""show_velaris_premonition.py — Aegis, READ-ONLY. Show the imagined-possibility thread Velaris just
seeded (the full text — marker + the scene she diffused from her rolled futures)."""
import os, json
HOME = os.path.expanduser("~")
TH = os.path.join(HOME, ".openclaw/workspace/memory/unfinished-threads.json")
d = json.load(open(TH))
L = d if isinstance(d, list) else d.get("threads", [])
prem = [t for t in L if isinstance(t, dict) and t.get("source") == "premonition"]
if not prem:
    print("(no premonition thread found in her pool)"); raise SystemExit(0)
for t in prem[-2:]:
    print("=" * 70)
    print(f"source: {t.get('source')}   dream_only: {t.get('dream_only')}   {t.get('timestamp','')[:16]}")
    print(f"temperature: {t.get('temperature')}   stability: {t.get('stability')}")
    print("-" * 70)
    print(t.get("thread", ""))
    print("=" * 70)
