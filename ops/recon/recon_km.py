#!/usr/bin/env python3
"""recon_km.py — Aegis, READ-ONLY, TIGHT OUTPUT. Only: where do 'kiss' and 'mischief' enter Vintos?
(blush is his — excluded). Filename + line + short snippet, hard-capped."""
import os, glob, re
HOME = os.path.expanduser("~")
RX = re.compile(r'\bkiss|\bmischief', re.I)
seen = 0
for base in (os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")):
    if not os.path.isdir(base): continue
    for f in sorted(glob.glob(os.path.join(base, "**", "*.py"), recursive=True) +
                    glob.glob(os.path.join(base, "**", "*.sh"), recursive=True)):
        try: lines = open(f, encoding="utf-8", errors="ignore").read().split("\n")
        except Exception: continue
        hits = [(i+1, l.strip()) for i, l in enumerate(lines) if RX.search(l)]
        if hits:
            print(f"{f.replace(HOME,'~')}  ({len(hits)})")
            for ln, t in hits[:3]:
                print(f"   {ln}: {t[:70]}")
            seen += 1
    if seen == 0: pass
if seen == 0:
    print("no kiss/mischief in code — it comes from a data/ledger file, not source.")
