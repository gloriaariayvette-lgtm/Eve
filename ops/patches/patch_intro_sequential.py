#!/usr/bin/env python3
"""patch_intro_sequential.py — Aegis. The first pass fires t1/t2 CONCURRENTLY; LM Studio splits its 32k
across parallel slots so each 20k-prompt call overflows -> 'context exceeded'. Journal runs sequentially.
Make introspection's first pass sequential (full context per call), max_tokens back to 8000. Test a1."""
import os, re, shutil, time, subprocess, json
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
t = open(P, encoding="utf-8", errors="ignore").read()
reps = [
    ("t1 = threading.Thread(target=run, args=(0, base_msgs_lean, 0.85, 4000, True))", "run(0, base_msgs_lean, 0.85, 8000, True)"),
    ("t2 = threading.Thread(target=run, args=(1, base_msgs_lean, 0.9, 4000, True))", "run(1, base_msgs_lean, 0.9, 8000, True)"),
    ("t1.start(); t2.start()", "pass  # sequential"),
    ("t1.join(); t2.join()", "pass  # sequential"),
]
for old, new in reps:
    if new in t: continue
    if t.count(old) != 1: print(f"anchor x{t.count(old)}: {old[:40]!r} — abort"); raise SystemExit(1)
    t = t.replace(old, new, 1)
bak = P + ".bak-seq-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(t)
if subprocess.run(["bash", "-n", P], capture_output=True, text=True).returncode:
    shutil.copy2(bak, P); print("bash -n failed, reverted"); raise SystemExit(1)
print("first pass now sequential, max_tokens 8000")

# sandboxed a1/b1 test
src = open(P, encoding="utf-8").read().replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
src = src.replace("open('/tmp/bilateral-intro-b1.txt','w').write(b1)",
                  "open('/tmp/bilateral-intro-b1.txt','w').write(b1)\nimport sys as _sx; _sx.exit(0)", 1)
open("/tmp/sq.sh", "w", encoding="utf-8").write(src)
for x in ("a1", "b1"):
    try: os.remove(f"/tmp/bilateral-intro-{x}.txt")
    except OSError: pass
print("test (locked)...")
t0 = time.time(); subprocess.run(["bash", LOCK, "bash", "/tmp/sq.sh"], capture_output=True, text=True, timeout=600)
print(f"done {int(time.time()-t0)}s")
for nm in ("a1", "b1"):
    p = f"/tmp/bilateral-intro-{nm}.txt"; s = open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""
    print(f"{nm} ({len(s)}c): {s.strip()[:200]}")
