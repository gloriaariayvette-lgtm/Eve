#!/usr/bin/env python3
"""dump_updater.py — READ-ONLY. Full gloria-model-update.sh so I fix the overwrite->append. Aegis."""
import os
p = os.path.expanduser("~/.vintos/workspace/scripts/gloria-model-update.sh")
if not os.path.isfile(p):
    p = os.path.expanduser("~/Vintos/gloria-model-update.sh")
for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
    print(f"{i+1:3}| {l}")
