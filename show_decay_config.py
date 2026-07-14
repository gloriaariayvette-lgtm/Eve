#!/usr/bin/env python3
"""show_decay_config.py — READ-ONLY, tiny. How DECAY_HALF_LIVES + BASELINE_EMOTION are defined in
emotion_model/config.py (list? dict? multiline? imported?). Aegis."""
import os, re
HOME = os.path.expanduser("~")
CFG = os.path.expanduser("~/.vintos/workspace/emotion_model/config.py")
ls = open(CFG, encoding="utf-8", errors="ignore").read().split("\n")
for key in ("DECAY_HALF_LIVES", "BASELINE_EMOTION", "DIMENSIONS", "DIMS"):
    idxs = [i for i, l in enumerate(ls) if re.search(rf'\b{key}\b', l)]
    print(f"=== {key} ===")
    if not idxs:
        print("  (not defined here)")
        continue
    for i in idxs[:2]:
        # print this line + continuation until brackets balance or ~14 lines
        block = ls[i]
        j = i
        while j+1 < len(ls) and (block.count("[")+block.count("{")) > (block.count("]")+block.count("}")) and j < i+16:
            j += 1; block += "\n" + ls[j]
        for k in range(i, j+1):
            print(f"  {k+1:4}| {ls[k][:150]}")
