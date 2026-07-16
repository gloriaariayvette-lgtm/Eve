#!/usr/bin/env python3
"""recon_journals.py — Aegis, READ-ONLY. Show how Vintos's journal + introspection scripts build their LLM
calls and bilateral (a1/b1/absorb/final) so they can get the a1/b1-Claude-reasoning + Claude-final treatment.
Terse, bounded."""
import os, re, glob
HOME = os.path.expanduser("~")
VDIR = os.path.join(HOME, "Vintos")
targets = ["idle-journal.sh", "vintos-journal.sh", "introspection.sh",
           "taste-reflection.py", "pride-mirror.py"]
RX = re.compile(r'api\.x\.ai|chat/completions|"model"|grok-4|curl|reasoning_effort|a1|b1|a2|b2|absorb|'
                r'integration|synth|final|gather|parallel|\bA1\b|\bB1\b|first.?pass|second.?pass', re.I)

for name in targets:
    p = os.path.join(VDIR, name)
    if not os.path.isfile(p):
        alt = glob.glob(os.path.join(VDIR, name.replace("-", "_"))) or glob.glob(os.path.join(VDIR, name.replace("_", "-")))
        p = alt[0] if alt else None
    if not p or not os.path.isfile(p):
        print(f"=== {name}: not found ==="); continue
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    hits = [(i+1, l.strip()) for i, l in enumerate(L) if l.strip() and RX.search(l)]
    print(f"\n===== {os.path.basename(p)}  ({len(L)} lines, {len(hits)} llm/bilateral hits) =====")
    for ln, t in hits[:34]:
        print(f"  {ln}: {t[:96]}")
    if len(hits) > 34: print(f"  ... +{len(hits)-34} more")
