#!/usr/bin/env python3
"""recon_cap3.py — Aegis, READ-ONLY. Answer: does CAPABILITIES.md carry hardware info?
Print its section headings and every line mentioning hardware/device terms."""
import os, re
p = os.path.expanduser("~/.vintos/workspace/memory/CAPABILITIES.md")
if not os.path.isfile(p):
    print("CAPABILITIES.md MISSING"); raise SystemExit(0)
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
print(f"CAPABILITIES.md — {len(L)} lines, {os.path.getsize(p)} bytes\n")
print("===== HEADINGS =====")
for i, l in enumerate(L):
    if l.lstrip().startswith("#"):
        print(f"  {i+1:>4}: {l.strip()[:100]}")
HW = re.compile(r'\b(lovense|device|hardware|motor|sensor|mission|tenera|cock|toy|vibrat|'
                r'buttplug|somatic|haptic|actuator|servo|TTS|Rex|voice|avatar|GPU|body)\b', re.I)
hits = [(i+1, l.strip()) for i, l in enumerate(L) if l.strip() and HW.search(l)]
print(f"\n===== HARDWARE-TERM LINES ({len(hits)}) =====")
for ln, t in hits[:40]:
    print(f"  {ln:>4}: {t[:110]}")
if len(hits) > 40: print(f"  ... +{len(hits)-40} more")
