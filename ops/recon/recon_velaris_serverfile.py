#!/usr/bin/env python3
"""recon_velaris_serverfile.py — Aegis, READ-ONLY. Dump Velaris's chat server bilateral block + _llm_call
helper with exact anchors so we can add reasoning_effort to the chat a1/b1 first-pass only (a2/b2 absorb,
held, integration stay no-think). File: /home/gloria/velaris-server/server.py."""
import os, re, glob
HOME = os.path.expanduser("~")
P = "/home/gloria/velaris-server/server.py"
def sh(p): return p.replace(HOME, "~")
if not os.path.isfile(P):
    # fallback: any server.py under velaris-server
    alt = glob.glob(os.path.join(HOME, "velaris-server", "**", "server.py"), recursive=True)
    P = alt[0] if alt else P
if not os.path.isfile(P):
    raise SystemExit("not found: " + P)
print("file:", sh(P))
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

print("\n===== _llm_call helper def + payload =====")
for i, l in enumerate(lines):
    if re.search(r'(async\s+)?def\s+_llm_call\b', l):
        for j in range(i, min(len(lines), i+30)):
            if lines[j].strip() and re.search(r'def |gemma-4-12b-qat|reasoning_effort|json=|payload|messages|temp|post\(|return', lines[j]):
                print(f"  {j+1}| {lines[j].strip()[:120]}")
            if j > i and re.match(r'\s*(async\s+)?def \w', lines[j]) and j != i: break

print("\n===== every a1, b1 = ... (first-pass) + absorb/held/integration calls =====")
for i, l in enumerate(lines):
    if re.search(r'a1,\s*b1\s*=|_absorb_msgs|_held_msgs|integration_messages|reply\s*=\s*await\s*_llm_call', l) and l.strip():
        print(f"  {i+1}| {l.strip()[:118]}")
print("\n(done — I'll flag a1/b1 gather calls, leave the rest)")
