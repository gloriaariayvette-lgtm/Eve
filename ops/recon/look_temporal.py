#!/usr/bin/env python3
"""look_temporal.py — READ-ONLY. Just temporal: the script(s) + what they output. Aegis."""
import os, re, glob, time

SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
VIN = os.path.expanduser("~/Vintos")
HOME = os.path.expanduser("~")

files = sorted(set(glob.glob(os.path.join(SCRIPTS, "*temporal*")) +
                   glob.glob(os.path.join(VIN, "*temporal*"))))
files = [f for f in files if os.path.isfile(f) and not f.endswith(".pyc")]
print("temporal files:", [f.replace(HOME, "~") for f in files] or "(none by name)")

for f in files:
    print(f"\n===== {f.replace(HOME,'~')} =====")
    for i, l in enumerate(open(f, encoding="utf-8", errors="ignore").read().split("\n")):
        if l.strip():
            print(f"{i+1:4}| {l[:170]}")

# its output
for c in ("temporal-context.json", "temporal-context.md", "temporal.json"):
    p = os.path.join(MEM, c)
    if os.path.isfile(p):
        print(f"\n===== OUTPUT {c}  (written {time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(p)))}) =====")
        print(open(p, encoding="utf-8", errors="ignore").read()[:800])

print("\nsystem clock now:", time.strftime("%Y-%m-%d %H:%M:%S %Z"))
