#!/usr/bin/env python3
"""recon_cap.py — Aegis, READ-ONLY. Find where idle-journal.sh and introspection.sh build their system prompt,
and whether CAPABILITIES.md (hardware info) is already loaded, so it can be injected for grounded reflection."""
import os, re
HOME = os.path.expanduser("~")
cap = os.path.join(HOME, ".vintos/workspace/memory/CAPABILITIES.md")
print(f"CAPABILITIES.md: {'EXISTS' if os.path.isfile(cap) else 'MISSING'} "
      f"({os.path.getsize(cap) if os.path.isfile(cap) else 0} bytes)  {cap.replace(HOME,'~')}\n")

RX = re.compile(r'CAPABILITIES|capabilit|system_msg\s*[-+]?=|^\s*system\s*=|SOUL\.md|soul\s*=|'
                r'\bidentity\s*=|read.*SOUL|_synthesis_system|base_msgs\s*=', re.I)
for name in ("idle-journal.sh", "introspection.sh"):
    p = os.path.join(HOME, "Vintos", name)
    if not os.path.isfile(p): print(f"=== {name}: not found ==="); continue
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    hits = [(i+1, l.strip()) for i, l in enumerate(L) if l.strip() and RX.search(l)]
    print(f"===== {name} ({len(hits)} hits) — has CAPABILITIES: {any('CAPABILIT' in l.upper() for _,l in hits)} =====")
    for ln, t in hits[:34]:
        print(f"  {ln}: {t[:104]}")
    if len(hits) > 34: print(f"  ... +{len(hits)-34} more")
    print()
