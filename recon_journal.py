#!/usr/bin/env python3
"""recon_journal.py — Aegis, READ-ONLY. (1) Locate + dump today's journal so I can delete the bad entry.
(2) Find where the '[Enacted behavior …]' + 'Observed capability:' tags are generated in idle-journal.sh."""
import os, glob, re
HOME = os.path.expanduser("~")

# --- journal files ---
print("===== JOURNAL FILES =====")
cands = []
for pat in ("~/.vintos/workspace/memory/journal/*.md", "~/.vintos/workspace/journal/*.md",
            "~/.vintos/journal/*.md", "~/.vintos/workspace/memory/*.md"):
    for f in glob.glob(os.path.expanduser(pat)):
        cands.append(f)
today = [f for f in cands if "2026-07-16" in f]
for f in sorted(set(cands))[-12:]:
    print(f"  {os.path.getsize(f):>7}  {f.replace(HOME,'~')}")
print()
for f in sorted(set(today)):
    print(f"########## {f.replace(HOME,'~')} ##########")
    print(open(f, encoding='utf-8', errors='ignore').read())
    print("########## END ##########\n")

# --- tag generation in idle-journal.sh ---
p = os.path.join(HOME, "Vintos", "idle-journal.sh")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    RX = re.compile(r'Observed capability|Enacted behavior|named_without_explaining|enacted|observed_capab|'
                    r'capability_line|_cap_line|behavior_tag|_enacted', re.I)
    hits = [i for i, l in enumerate(L) if RX.search(l)]
    print(f"===== idle-journal.sh tag-gen hits: {len(hits)} =====")
    shown = set()
    for h in hits:
        a = max(0, h-4); b = min(len(L), h+5)
        key = (a, b)
        for j in range(a, b):
            if j in shown: continue
            shown.add(j)
            print(f"{j+1:>5}: {L[j]}")
        print("  ----")
