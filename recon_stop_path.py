#!/usr/bin/env python3
"""recon_stop_path.py — Aegis, READ-ONLY. Certify Inviolable B (emergency stop). Show: (1) server.py the region
that owns device stop (~7600-7790) incl. its @app route + where it SENDS the stop to the device + whether it's a
lightweight path (no LLM/queue), (2) every place 'stopped' is set True, (3) somatic_bridge.py's watchdog / device
disconnect handling (broadened search: socket close, reconnect, ConnectionClosed, motor 0)."""
import os, re
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")
SCR = os.path.expanduser("~/.vintos/workspace/scripts")

print("===== (1) server.py device-stop region (7600-7790): route + raw send =====")
S = open(os.path.join(V, "server.py"), encoding="utf-8", errors="ignore").read().split("\n")
for i in range(7595, 7790):
    if i < len(S):
        l = S[i]
        if re.search(r'@app\.|def |stop|192\.168|ws://|websocket|send|\.post\(|heartbeat|_hb|device|mission|tenera|queue|await|return', l, re.I):
            print("  %d: %s" % (i + 1, l.strip()[:104]))

print("\n===== (2) everywhere 'stopped' is SET True (the trigger) =====")
for i, l in enumerate(S):
    if re.search(r'stopped[\"\']?\]?\s*=\s*True|\[.stopped.\]\s*=\s*True|"stopped":\s*True', l):
        print("  %d: %s" % (i + 1, l.strip()[:104]))

print("\n===== (3) somatic_bridge.py — watchdog / disconnect / motor-off (broad) =====")
p = os.path.join(SCR, "somatic_bridge.py")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(L):
        if re.search(r'watchdog|heartbeat|Connection|closed|reconnect|except|timeout|\bstop\b|motor|0\.0|send|ws|socket|def ', l, re.I):
            print("  %d: %s" % (i + 1, l.strip()[:104]))
else:
    print("  somatic_bridge.py NOT FOUND")
