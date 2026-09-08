#!/usr/bin/env python3
"""revert_conflict_surface.py — Aegis. Undo the mistaken reasoning_effort patch on conflict_surface.py
(it's the friction-naming stage, not a1/b1). Restore from its .bak-think-* backup, or strip the token."""
import os, glob, shutil
HOME = os.path.expanduser("~")
p = os.path.join(HOME, ".vintos/workspace/scripts/conflict_surface.py")
baks = sorted(glob.glob(p + ".bak-think-*"))
if baks:
    shutil.copy2(baks[-1], p)
    print("reverted from", baks[-1].replace(HOME, "~"))
else:
    txt = open(p, encoding="utf-8").read()
    if '"reasoning_effort":"high",' in txt:
        open(p, "w", encoding="utf-8").write(txt.replace('"reasoning_effort":"high",', "", 1))
        print("no backup found — stripped the reasoning_effort token")
    else:
        print("nothing to revert (already clean)")
