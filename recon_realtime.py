#!/usr/bin/env python3
"""recon_realtime.py — Aegis, READ-ONLY, TIGHT. realtime_causality.py runs every 20 min. Does it also mint
causeless 'emerged/untraceable/low-confidence' hypotheses into the unresolved pile? Show its record/write points
+ any untraceable/confidence handling. Also peek causal-cluster.py's hypothesis gate. Capped."""
import os, re
HOME = os.path.expanduser("~")
for name in ("realtime_causality.py", "causal-cluster.py"):
    for base in (os.path.join(HOME, ".vintos/workspace/scripts"), os.path.join(HOME, "Vintos")):
        p = os.path.join(base, name)
        if not os.path.isfile(p): continue
        L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        print(f"===== {p.replace(HOME,'~')} ({len(L)} lines) =====")
        RX = re.compile(r'untraceable|no traceable|emerged|no (clear )?cause|idk|unexplain|'
                        r'confidence|append.*hypoth|hypotheses.*append|setdefault\("hypoth|'
                        r'unfinished-threads|add_hypothesis|json\.dump|threshold', re.I)
        shown = set()
        for i, l in enumerate(L):
            if RX.search(l):
                for j in range(max(0, i-1), min(len(L), i+2)):
                    if j in shown: continue
                    shown.add(j); print(f"  {j+1}: {L[j].strip()[:94]}")
                print("   ..")
        break
    print()
