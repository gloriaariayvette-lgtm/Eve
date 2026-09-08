#!/usr/bin/env python3
"""show_source.py — READ-ONLY, capped. Is emoclaw.yaml present (and its decay_hours), or does config.py
use baked-in defaults? Show whichever actually holds the numbers. Aegis."""
import os, re, subprocess
HOME = os.path.expanduser("~")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout

print("=== emoclaw.yaml locations ===")
y = run(["bash","-lc","find ~/.vintos ~/Vintos -name emoclaw.yaml 2>/dev/null | grep -v node_modules"]).strip().split("\n")
y = [p for p in y if p]
print("  found:", [p.replace(HOME,'~') for p in y] or "(none -> config.py defaults are used)")
for p in y[:1]:
    print(f"  -- {p.replace(HOME,'~')} : dimension/decay lines --")
    n = 0
    for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'decay|name:|baseline|Connection|Warmth|Groundedness|dimensions', l, re.I):
            print(f"     {i+1:4}| {l[:120]}"); n += 1
            if n >= 30: break

print("\n=== config.py — the default dimension table (decay_hours) ===")
CFG = os.path.expanduser("~/.vintos/workspace/emotion_model/config.py")
ls = open(CFG, encoding="utf-8", errors="ignore").read().split("\n")
hits = [i for i, l in enumerate(ls) if "decay_hours" in l]
print("  'decay_hours' appears on lines:", [h+1 for h in hits][:12])
for i in hits[:4]:
    for k in range(max(0, i-1), min(i+2, len(ls))):
        print(f"  {k+1:4}| {ls[k][:150]}")
    print("  ---")
