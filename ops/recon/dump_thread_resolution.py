#!/usr/bin/env python3
"""dump_thread_resolution.py — Aegis, READ-ONLY. Triage spawns thread-resolution.py dissolve/sediment/
resolve — the likely mass-consumer. Print it full so I see what it removes and on what condition."""
import os
WS = os.path.expanduser("~/.openclaw/workspace")
p = next((os.path.join(WS,"scripts",n) for n in ("thread-resolution.py","thread_resolution.py")
          if os.path.isfile(os.path.join(WS,"scripts",n))), None)
if not p: raise SystemExit("thread-resolution not found")
print("FILE:", p.replace(os.path.expanduser("~"), "~"), "\n")
for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
    print(f"{i+1:4}| {l}")
