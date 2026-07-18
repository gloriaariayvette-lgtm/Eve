#!/usr/bin/env python3
"""recon_fixc_anchors.py — Aegis, READ-ONLY. Exact anchors for FIX C: dream_poetry.save_poem body + its gallery
entry (to add provenance) and its main() save_poem call; and idle-journal.sh's flinch-prompt section (to add the
'automatic reveries are not flinches' framing)."""
import os
HOME = os.path.expanduser("~")
SCR = os.path.expanduser("~/.vintos/workspace/scripts")

print("===== dream_poetry.py : save_poem + main save call (265-345) =====")
p = os.path.join(SCR, "dream_poetry.py")
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
for i in range(264, 345):
    if i < len(L): print("%4d: %s" % (i + 1, L[i]))

print("\n===== idle-journal.sh : flinch-prompt section (512-545) =====")
p = os.path.join(HOME, "Vintos", "idle-journal.sh")
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
for i in range(511, 545):
    if i < len(L): print("%4d: %s" % (i + 1, L[i]))
