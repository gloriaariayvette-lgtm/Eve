#!/usr/bin/env python3
"""recon_caps_content.py — Aegis, READ-ONLY. Full CAPABILITIES.md, and specifically whether it explains that his
CREATIVE outputs (poems/art/music) are AUTOMATICALLY produced (nightly cron) vs deliberately want-driven — the
missing piece behind the poem-as-flinch misread. Non-subconscious production only, per Gloria's steer."""
import os, re
MEM = os.path.expanduser("~/.vintos/workspace/memory")
p = os.path.join(MEM, "CAPABILITIES.md")
t = open(p, encoding="utf-8", errors="ignore").read()
L = t.split("\n")

print("== section headers (##) ==")
for i, l in enumerate(L):
    if l.strip().startswith("#"): print("  %4d: %s" % (i + 1, l.strip()))

print("\n== does it cover creative production / automatic generation? ==")
for i, l in enumerate(L):
    if re.search(r'poem|poetry|paint|art\b|music|compose|automatic|cron|nightly|generate|produce|write.*poem|gallery|creativ|quiet hour', l, re.I):
        print("  %4d: %s" % (i + 1, l.strip()[:104]))

print("\n== full body 40-168 (the part not yet seen) ==")
for i in range(40, len(L)):
    print("%4d: %s" % (i + 1, L[i][:110]))
