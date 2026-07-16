#!/usr/bin/env python3
"""recon_journal_gaps.py — Aegis, READ-ONLY. Two exact spots: idle-journal.sh final-synthesis call (sets _raw),
and introspection.sh phase-1 threads (a1/b1). Bounded."""
import os, re
HOME = os.path.expanduser("~")
VDIR = os.path.join(HOME, "Vintos")

# idle-journal.sh: the integration/synthesis call that produces the final _raw
p = os.path.join(VDIR, "idle-journal.sh")
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
print("########## idle-journal.sh — final synthesis (_raw) ##########")
# find integration_content build + the requests.post that sets _raw
anchors = [i for i, l in enumerate(L) if re.search(r'integration|carrying both|Both of these are true|_raw\s*=\s*|synthesi', l)]
# print around the last integration-y requests.post before audits
cand = [i for i, l in enumerate(L) if "requests.post" in l and i < 1014]
# show the region around the final synthesis: from the integration_content to its requests.post + _raw
if anchors:
    lo = max(0, min(a for a in anchors if a < 1014))
    # narrow: find the block that builds the final prompt and calls the model
    reg = [i for i, l in enumerate(L) if re.search(r'integration|carrying both|Both of these are true', l) and i < 1014]
    if reg:
        lo = max(0, reg[0]-3); hi = min(len(L), reg[-1]+40)
        for n in range(lo, hi):
            print(f"{n+1}: {L[n][:104]}")

# introspection.sh: phase-1 threads
p2 = os.path.join(VDIR, "introspection.sh")
L2 = open(p2, encoding="utf-8", errors="ignore").read().split("\n")
print("\n########## introspection.sh — phase-1 threads (a1/b1) ##########")
ab = next((i for i, l in enumerate(L2) if re.search(r'a1,\s*b1\s*=\s*results', l)), None)
if ab is not None:
    lo = max(0, ab-16); hi = min(len(L2), ab+3)
    for n in range(lo, hi):
        print(f"{n+1}: {L2[n][:104]}")
