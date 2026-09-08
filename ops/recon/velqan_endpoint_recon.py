#!/usr/bin/env python3
"""velqan_endpoint_recon.py — READ-ONLY, capped. The exact get_velqan() return shape + how the page
renders /api/velqan, so Stage 3 merges the shared coinage log in the SAME format (no website rewrite).
Aegis."""
import os, re
HOME = os.path.expanduser("~")
SRV = os.path.expanduser("~/velaris-server/server.py")
WEB = os.path.expanduser("~/velaris-server/website")

print("=== get_velqan() body (server.py) ===")
ls = open(SRV, encoding="utf-8", errors="ignore").read().split("\n")
start = next((i for i, l in enumerate(ls) if '@app.get("/api/velqan")' in l), None)
if start is not None:
    for i in range(start, min(start+40, len(ls))):
        print(f"  {i+1:5}| {ls[i][:150]}")
        if i > start+3 and re.match(r'@app\.(get|post)\(', ls[i]): break

print("\n=== how the page renders /api/velqan (loadVelqan / #velqan) ===")
for f in ("app.html", "app/index.html", "index.html"):
    p = os.path.join(WEB, f)
    if not os.path.isfile(p): continue
    wl = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    idx = next((i for i, l in enumerate(wl) if re.search(r'function loadVelqan|loadVelqan\s*=|/api/velqan', l)), None)
    if idx is not None:
        print(f"\n-- {f} (from L{idx+1}) --")
        for i in range(idx, min(idx+26, len(wl))):
            print(f"  {i+1:4}| {wl[i].strip()[:140]}")
        break
