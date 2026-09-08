#!/usr/bin/env python3
"""Edit only, no LLM call. Lower introspection first-pass max_tokens 8000->6000 so prompt+reasoning fit 32k.
Nothing cut. Backup + bash -n."""
import os, shutil, time, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
t = open(P, encoding="utf-8", errors="ignore").read()
if ", 6000, True)" in t:
    print("already 6000")
elif t.count(", 8000, True)"):
    bak = P + ".bak-6k-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
    open(P, "w", encoding="utf-8").write(t.replace(", 8000, True)", ", 6000, True)"))
    if subprocess.run(["bash", "-n", P], capture_output=True, text=True).returncode:
        shutil.copy2(bak, P); print("bash -n failed, reverted"); raise SystemExit(1)
    print("introspection first-pass max_tokens -> 6000 (nothing cut, backup saved)")
else:
    print("no ', 8000, True)' found — current max_tokens differs")
