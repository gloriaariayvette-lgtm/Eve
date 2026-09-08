#!/usr/bin/env python3
"""recon_preoc_setter.py — Aegis, READ-ONLY, capped. Dreams read get_preoccupation(); the seed is chosen
by whoever calls set_preoccupation() (or picks the thread the dream cycle dreams). Find that selection so
'dreams seek heat' biases the right spot toward highest temperature. Show every set_preoccupation caller
+ how it picks the thread, and the dream-cycle seed source."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
def sh(p): return p.replace(HOME, "~")

print("=== every set_preoccupation() caller (who chooses the dream seed) ===")
hits = subprocess.run(["bash","-lc",
    f"grep -rnE 'set_preoccupation\\(' {SC} 2>/dev/null | grep -viE '\\.bak|\\.pyc|def set_preoccupation' | head -20"],
    capture_output=True, text=True).stdout.strip()
print(hits.replace(HOME, "~") or "  (none)")

print("\n=== how each caller selects the thread it promotes (context around the call) ===")
files = set()
for line in hits.split("\n"):
    if ":" in line:
        files.add(line.split(":", 1)[0])
for f in sorted(files)[:5]:
    if not os.path.isfile(f):
        continue
    lines = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    idxs = [i for i, l in enumerate(lines) if "set_preoccupation(" in l and "def " not in l]
    print(f"  -- {sh(f)} --")
    for i in idxs[:2]:
        for j in range(max(0, i - 6), min(len(lines), i + 2)):
            if lines[j].strip():
                print(f"   {'>>' if j==i else '  '}{j+1:4}| {lines[j].strip()[:104]}")

print("\n=== the dream cycle: what it dreams (preoccupation vs hottest thread) ===")
for name in ("preoccupation-dream.sh", "dream-architecture.sh", "should-dream.sh", "dream-cycle.sh"):
    p = os.path.join(SC, name)
    if not os.path.isfile(p):
        continue
    lines = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"  -- {name} ({len(lines)} lines) --")
    n = 0
    for i, l in enumerate(lines):
        if re.search(r'get_preoccupation|preoccupation|unconsumed|thread|seed|dream_text|priority|temperature|sort|\.get\(', l, re.I) \
           and l.strip() and not l.strip().startswith("#"):
            print(f"   {i+1:4}| {l.strip()[:104]}")
            n += 1
            if n >= 12:
                break
