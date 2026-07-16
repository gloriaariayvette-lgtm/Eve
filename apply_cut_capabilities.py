#!/usr/bin/env python3
"""apply_cut_capabilities.py — Aegis. Edit only, no LLM call. Cut CAPABILITIES from introspection prompt
(journal-sizes it to ~20k). Backup + bash -n."""
import os, shutil, time, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
t = open(P, encoding="utf-8", errors="ignore").read()
c = '$(cat "$WORKSPACE/memory/CAPABILITIES.md")'
if c in t:
    bak = P + ".bak-cutcap-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
    open(P, "w", encoding="utf-8").write(t.replace(c, '""', 1))
    if subprocess.run(["bash", "-n", P], capture_output=True, text=True).returncode:
        shutil.copy2(bak, P); print("bash -n failed, reverted"); raise SystemExit(1)
    print("cut CAPABILITIES from introspection (backup saved)")
else:
    print("CAPABILITIES already cut / anchor not found")
