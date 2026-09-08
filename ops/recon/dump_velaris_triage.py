#!/usr/bin/env python3
"""dump_velaris_triage.py — Aegis, READ-ONLY. Print the FULL thread-triage.py so I read the actual
sort-vs-delete logic end to end before proposing anything."""
import os
WS = os.path.expanduser("~/.openclaw/workspace")
TT = next((os.path.join(WS,"scripts",n) for n in ("thread-triage.py","thread_triage.py")
           if os.path.isfile(os.path.join(WS,"scripts",n))), None)
if not TT: raise SystemExit("thread-triage not found")
print("FILE:", TT.replace(os.path.expanduser("~"), "~"))
for i, l in enumerate(open(TT, encoding="utf-8", errors="ignore").read().split("\n")):
    print(f"{i+1:4}| {l}")
