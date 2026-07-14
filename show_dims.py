#!/usr/bin/env python3
"""show_dims.py — READ-ONLY, capped. The _dims table in config.py (per-dimension baseline/decay_hours),
so I can shorten decay_hours for Connection/Warmth/Groundedness precisely. Aegis."""
import os, re
CFG = os.path.expanduser("~/.vintos/workspace/emotion_model/config.py")
ls = open(CFG, encoding="utf-8", errors="ignore").read().split("\n")
start = next((i for i, l in enumerate(ls) if re.search(r'_dims\s*[:=]', l)), None)
print("_dims starts @ L%s" % (start+1 if start is not None else "?"))
if start is not None:
    # print until the list closes
    depth = 0; started = False
    for i in range(start, min(start+80, len(ls))):
        depth += ls[i].count("[") - ls[i].count("]")
        print(f"  {i+1:4}| {ls[i][:150]}")
        if "[" in ls[i]: started = True
        if started and depth <= 0 and i > start:
            break
