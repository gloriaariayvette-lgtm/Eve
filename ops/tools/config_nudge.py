#!/usr/bin/env python3
"""config_nudge.py — READ-ONLY, capped. (1) his DECAY_HALF_LIVES + BASELINE_EMOTION values to sharpen
Connection/Warmth/Groundedness. (2) which chat handlers actually CALL nudge_emotions_from_text. Aegis."""
import os, re, subprocess
HOME = os.path.expanduser("~")
TS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")
SERVER = os.path.expanduser("~/Vintos/server.py")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout

print("=== 1) DECAY config (DECAY_HALF_LIVES + BASELINE_EMOTION) ===")
cfg = run(["bash","-lc", f"grep -rln 'DECAY_HALF_LIVES' {TS} {VIN} 2>/dev/null | grep -viE '\\.bak|\\.pyc' | head -2"]).split()
print("  config file:", [c.replace(HOME,'~') for c in cfg] or "(not found)")
for c in cfg[:1]:
    ls = open(c, encoding="utf-8", errors="ignore").read().split("\n")
    # print the DIMS/BASELINE/HALF_LIVES definitions (may span lines)
    for i, l in enumerate(ls):
        if re.search(r'DECAY_HALF_LIVES|BASELINE_EMOTION|^DIMS|DIMENSIONS\s*=', l):
            # print this line + up to 3 continuation lines if it's a bracketed list
            block = l
            j = i
            while ("[" in block and "]" not in block) and j+1 < len(ls) and j < i+4:
                j += 1; block += " " + ls[j].strip()
            print(f"  {i+1:4}| {block.strip()[:260]}")

print("\n=== 2) which handlers CALL nudge_emotions_from_text( ? ===")
ls = open(SERVER, encoding="utf-8", errors="ignore").read().split("\n")
calls = [i for i, l in enumerate(ls) if re.search(r'nudge_emotions_from_text\s*\(', l)]
print(f"  {len(calls)} call site(s) (def is one of them):")
for i in calls[:14]:
    # find nearest preceding @app route or def for context
    ctx = ""
    for k in range(i, max(0, i-60), -1):
        m = re.search(r'@app\.\w+\("([^"]+)"\)|async def (\w+)', ls[k])
        if m: ctx = m.group(1) or m.group(2); break
    print(f"  {i+1:5}| [{ctx}] {ls[i].strip()[:110]}")
if len(calls) <= 1:
    print("  !! only the definition — it's essentially never called from chat. That's the silence.")
