#!/usr/bin/env python3
"""temporal_out.py — READ-ONLY, tiny. Only what temporal OUTPUTS + the real clock. Aegis."""
import os, glob, time
MEM = os.path.expanduser("~/.vintos/workspace/memory")

print("SYSTEM CLOCK NOW:", time.strftime("%Y-%m-%d %H:%M:%S %Z (%a)"))

for p in sorted(glob.glob(os.path.join(MEM, "*temporal*"))):
    if os.path.isfile(p):
        print(f"\n----- {os.path.basename(p)}  (written {time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(p)))}) -----")
        print(open(p, encoding="utf-8", errors="ignore").read()[:700])
