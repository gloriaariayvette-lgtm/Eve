#!/usr/bin/env python3
"""recon_poem.py — Aegis, READ-ONLY, TIGHT. Name the script that WRITES the poems into daily-creative,
and show how kiss/mischief reach its seed. <25 lines out."""
import os, glob, re
HOME = os.path.expanduser("~")
# scripts that WRITE poetry (append '## Poetry' or write daily-creative), not just reference it
for f in sorted(glob.glob(os.path.join(HOME, "Vintos", "*.py")) + glob.glob(os.path.join(HOME, "Vintos", "*.sh"))):
    try: txt = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    L = txt.split("\n")
    writes_poetry = any(("## Poetry" in l and ("append" in l.lower() or "write" in l.lower() or '>>' in l or 'echo' in l.lower() or 'f.write' in l.lower())) for l in L) \
                    or any("Poetry" in l and ("def " in l or "poem" in l.lower()) for l in L) \
                    or "poem" in os.path.basename(f).lower()
    if writes_poetry:
        km = [(i+1, l.strip()[:85]) for i, l in enumerate(L) if re.search(r'\bkiss|\bmischief|near-miss|near_miss', l, re.I)]
        print(f"== {os.path.basename(f)} == kiss/mischief hits: {len(km)}")
        for ln, t in km[:8]:
            print(f"   {ln}: {t}")
