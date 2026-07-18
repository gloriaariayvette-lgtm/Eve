#!/usr/bin/env python3
"""recon_inviolables.py — Aegis, READ-ONLY. VERIFY (not rebuild) the two somatic Inviolables:
(A) Input comprehension stays 100% — bandwidth_collapse gates OUTPUT only, never the reading of Gloria's message.
(B) Emergency stop on an independent raw path — an immediate motor/device STOP that bypasses state/queues/LLM.
Dumps bandwidth_collapse.py, the somatic_bridge watchdog/stop functions, and every stop/emergency route in server.py."""
import os, re
HOME = os.path.expanduser("~")
SCR = os.path.expanduser("~/.vintos/workspace/scripts")
V = os.path.join(HOME, "Vintos")

def find(name):
    for d in (SCR, V):
        p = os.path.join(d, name)
        if os.path.isfile(p): return p
    return None

print("===== (A) bandwidth_collapse.py — is collapse OUTPUT-only? (input carve-out) =====")
p = find("bandwidth_collapse.py")
if p:
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    print("  %s (%dL)" % (p, len(L)))
    for i, l in enumerate(L):
        if i < 8 or re.search(r'input|comprehen|parse|output|generat|level\s*3|tier|inviolab|def ', l, re.I):
            print("   %d: %s" % (i + 1, l.strip()[:100]))
else:
    print("  bandwidth_collapse.py NOT FOUND")

print("\n===== (B1) somatic_bridge.py — watchdog + stop/emergency functions =====")
p = find("somatic_bridge.py")
if p:
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(L):
        if re.search(r'watchdog|heartbeat|def .*stop|motor.?stop|emergenc|\bstop\b|kill|panic|all_stop|/stop|raw', l, re.I):
            print("   %d: %s" % (i + 1, l.strip()[:100]))
else:
    print("  somatic_bridge.py NOT FOUND")

print("\n===== (B2) server.py — stop / emergency routes (independent raw path) =====")
S = open(os.path.join(V, "server.py"), encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(S):
    if re.search(r'@app\.(post|get)\([^)]*stop|def .*stop|emergenc|motor.?stop|all[_-]?stop|panic|/api/[^"]*stop|device.*stop|lovense.*stop', l, re.I):
        for j in range(i, min(len(S), i + 3)):
            print("   %d: %s" % (j + 1, S[j].strip()[:100]))
        print("    --")
