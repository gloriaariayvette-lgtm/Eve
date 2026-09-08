#!/usr/bin/env python3
"""recon_bridge.py — Aegis, READ-ONLY. What does the somatic bridge connect to (so Gloria reconnects the right
source)? Show its websocket target/connect code, device-state, and the full recent bridge log."""
import os, re, subprocess
HOME = os.path.expanduser("~")

print("== bridge connection target (ws url / connect) ==")
for name in ("somatic_bridge.py", "vintos-ear.py", "somatic-bridge.py"):
    for base in (os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")):
        p = os.path.join(base, name)
        if not os.path.isfile(p): continue
        L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        print(f"  --- {name} ---")
        for i, l in enumerate(L):
            if re.search(r'ws://|wss://|connect\(|websockets?\.|listen|serve|host|port|intiface|lovense|url\s*=|ADDR|0\.0\.0\.0|127\.0\.0\.1|:\d{4}', l, re.I):
                print(f"    {i+1}: {l.strip()[:100]}")

print("\n== device-state.json ==")
p = os.path.join(HOME, ".vintos/workspace/memory/device-state.json")
if os.path.isfile(p): print("  " + open(p).read()[:300])

print("\n== full recent bridge log (20 lines) ==")
r = subprocess.run(["journalctl", "--user", "-u", "vintos-somatic-bridge", "-n", "20", "--no-pager"], capture_output=True, text=True)
print(r.stdout or r.stderr)

print("== is the unit even the right name? ==")
r2 = subprocess.run(["systemctl", "--user", "list-units", "--all", "--no-pager"], capture_output=True, text=True)
for line in (r2.stdout or "").split("\n"):
    if "somatic" in line.lower() or "bridge" in line.lower() or "ear" in line.lower() or "lovense" in line.lower():
        print("  " + line.strip())
