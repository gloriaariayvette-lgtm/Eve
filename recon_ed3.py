#!/usr/bin/env python3
"""recon_ed3.py — Aegis, READ-ONLY, TIGHT. (A) Exact diff of Vintos vs Velaris enactment_distiller.py — is his a
faithful clone or subtly changed? (B) Show how identity_candidate becomes the 'Observed capability:' journal line
(the render/process path). Small output."""
import os, difflib, re
HOME = os.path.expanduser("~")
V = os.path.join(HOME, ".vintos/workspace/scripts/enactment_distiller.py")
O = os.path.join(HOME, ".openclaw/workspace/scripts/enactment_distiller.py")

print("===== (A) DIFF  vintos (-)  vs  velaris (+)  =====")
if os.path.isfile(V) and os.path.isfile(O):
    vl = open(V, encoding="utf-8", errors="ignore").read().split("\n")
    ol = open(O, encoding="utf-8", errors="ignore").read().split("\n")
    d = list(difflib.unified_diff(vl, ol, "vintos", "velaris", lineterm=""))
    if len(d) <= 2:
        print("  IDENTICAL (no differences at all)")
    else:
        for l in d[:80]: print(" " + l[:118])
else:
    print("  (one or both files missing)")

print("\n===== (B) how 'Observed capability' / identity_candidate is rendered (vintos file) =====")
if os.path.isfile(V):
    L = open(V, encoding="utf-8", errors="ignore").read().split("\n")
    RX = re.compile(r'Observed capability|identity_candidate|Enacted behavior|def process|append.*journal|journal.*append|\.md', re.I)
    shown = set()
    for i, l in enumerate(L):
        if RX.search(l):
            for j in range(max(0, i-2), min(len(L), i+4)):
                if j not in shown:
                    shown.add(j); print(f"{j+1:>4}: {L[j][:116]}")
            print("   ..")
