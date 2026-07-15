#!/usr/bin/env python3
"""force_gloria_update.py — Aegis. Force a REAL gloria-model-update.sh run now, and verify the fixed base
came through untouched: hash the BASE-START..BASE-END region before and after — they MUST match — then show
the new dated addition it appended. This is a live run (his real model), authorized. Output capped."""
import os, re, hashlib, subprocess, time
WS = os.path.expanduser("~/.vintos/workspace")
GM = os.path.join(WS, "GLORIA-MODEL.md")
UPD = os.path.join(WS, "scripts", "gloria-model-update.sh")
if not os.path.isfile(UPD):
    UPD = os.path.expanduser("~/Vintos/gloria-model-update.sh")

def base_region(path):
    if not os.path.isfile(path): return ""
    t = open(path, encoding="utf-8", errors="ignore").read()
    m = re.search(r"<!-- BASE-START.*?<!-- BASE-END -->", t, re.DOTALL)
    return m.group(0) if m else ""

before = base_region(GM)
h_before = hashlib.sha256(before.encode()).hexdigest()[:16]
print(f"base before: {len(before)}B  sha={h_before}")

print(f"running {os.path.basename(UPD)} (real, grok) ...")
t0 = time.time()
r = subprocess.run(["bash", UPD], capture_output=True, text=True, timeout=300)
print(f"exit={r.returncode}  {time.time()-t0:.0f}s")
tail = (r.stderr or r.stdout or "").strip().split("\n")[-4:]
if any(x.strip() for x in tail): print("  log tail:", " | ".join(x[:100] for x in tail if x.strip()))

after = base_region(GM)
h_after = hashlib.sha256(after.encode()).hexdigest()[:16]
print(f"base after:  {len(after)}B  sha={h_after}  ->", "IDENTICAL ✓ (base untouched)" if h_after == h_before and before else "⚠ CHANGED — check")

# show the newest addition it wrote (header + first lines only)
t = open(GM, encoding="utf-8", errors="ignore").read()
add = t.split("# Additions", 1)[-1]
secs = re.findall(r"(^## .+?)(?=^## |\Z)", add, re.DOTALL | re.MULTILINE)
if secs:
    newest = secs[0].strip().split("\n")
    print("\nnewest addition:")
    for l in newest[:10]:
        print("  " + l[:96])
    if len(newest) > 10: print(f"  ... (+{len(newest)-10} more lines)")
