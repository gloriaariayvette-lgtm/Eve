#!/usr/bin/env python3
"""recon_causality3.py — Aegis, READ-ONLY, TIGHT. Verbatim of the three causality write points so I can suppress
causeless 'emotion changed idk why' hypotheses at the source: find_spikes threshold, add_hypothesis, JEPA record."""
import os
p = os.path.expanduser("~/Vintos/causality-engine.py")
if not os.path.isfile(p): print("causality-engine.py not found"); raise SystemExit(0)
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
for a, b, tag in ((115, 140, "find_spikes"), (878, 945, "add_hypothesis"), (985, 1032, "JEPA record")):
    print(f"----- {tag}: L{a}-{b} -----")
    for i in range(a-1, min(len(L), b)):
        print(f"{i+1:>4}: {L[i]}")
    print()
