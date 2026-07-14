#!/usr/bin/env python3
"""daemon_process_cmd.py — READ-ONLY, tiny. Exact 'process_message' command handler (name + fields +
response) so I wire chat -> model correctly. Aegis."""
import os
d = os.path.expanduser("~/.openclaw/workspace/emotion_model/daemon.py")
ls = open(d, encoding="utf-8", errors="ignore").read().split("\n")
# print the region around process_message (108-145)
for i in range(107, min(146, len(ls))):
    print(f"{i+1:4}| {ls[i][:150]}")
print("\n--- inference.process_message signature ---")
inf = os.path.expanduser("~/.openclaw/workspace/emotion_model/inference.py")
il = open(inf, encoding="utf-8", errors="ignore").read().split("\n")
start = next((i for i,l in enumerate(il) if "def process_message" in l), None)
if start is not None:
    for i in range(start, min(start+16, len(il))):
        print(f"{i+1:4}| {il[i][:150]}")
