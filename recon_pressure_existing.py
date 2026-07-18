#!/usr/bin/env python3
"""recon_pressure_existing.py — Aegis, READ-ONLY, FAST (specific files). Before building the spark's Pressure,
reconcile with what already exists: relationship_pressure.py, self_pressure.py, pressure_gemma.py. For each: def
signatures, what it reads/writes (json/memory), and whether it already does any of the spark's Pressure pieces —
force_directive / demand_response / a timeliness or outreach gate / asymmetric stall detection / self_drift push /
source="pressure". Also: does it already call record_direction_choice, and is there a pressure-events store?
Tells us whether the spark Pressure EXTENDS these or is genuinely new. Nothing written."""
import os, re
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")
MEM = os.path.expanduser("~/.vintos/workspace/memory")

FILES = ["relationship_pressure.py", "self_pressure.py", "pressure_gemma.py", "relationship-pressure.py"]
SPARK = re.compile(r'force_directive|demand_response|timeliness|outreach.?gate|asymmetric|stall|'
                   r'record_direction_choice|source\s*=\s*["\']pressure|pressure.?event|apply_pressure|'
                   r'get_direction_bias|initiate|reach.?first', re.I)

for name in FILES:
    p = os.path.join(HIS, name)
    if not os.path.isfile(p):
        continue
    t = open(p, encoding="utf-8", errors="ignore").read()
    L = t.split("\n")
    print("\n===== %s (%d lines) =====" % (name, len(L)))
    # docstring first lines
    doc = re.search(r'"""(.*?)"""', t, re.S)
    if doc:
        for dl in doc.group(1).strip().split("\n")[:4]:
            print("   | " + dl.strip()[:104])
    print("  -- defs --")
    for i, l in enumerate(L):
        if re.match(r'\s*def\s', l):
            print("    %4d: %s" % (i + 1, l.strip()[:96]))
    print("  -- reads/writes --")
    for i, l in enumerate(L):
        if re.search(r'\.json|MEMORY|open\(|json\.dump|json\.load|requests\.|GEMMA|:8599|:1234', l):
            print("    %4d: %s" % (i + 1, l.strip()[:96]))
        if i > 400: break
    print("  -- overlaps with spark Pressure --")
    hits = [(i + 1, l.strip()[:96]) for i, l in enumerate(L) if SPARK.search(l)]
    for i, l in hits[:20]:
        print("    %4d: %s" % (i, l))
    if not hits:
        print("    (none — no force_directive/stall/self_drift push/pressure-source here)")

print("\n== is relationship_pressure / self_pressure wired into cron or the server/outreach? ==")
import subprocess
cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
for l in cur.split("\n"):
    if re.search(r'pressure', l, re.I) and l.strip():
        print("  cron| " + l.strip()[:110])
# who imports these pressure modules?
for base in (HIS, VIN):
    if not os.path.isdir(base): continue
    for e in os.scandir(base):
        if not e.is_file() or not e.name.endswith(".py"): continue
        try: t = open(e.path, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        if re.search(r'import (relationship_pressure|self_pressure|pressure_gemma)|from (relationship_pressure|self_pressure|pressure_gemma)', t):
            print("  imports pressure: %s" % e.name)

print("\n== existing pressure/directive stores in memory ==")
if os.path.isdir(MEM):
    for e in os.scandir(MEM):
        if e.is_file() and re.search(r'pressure|directive|stall', e.name, re.I):
            print("  %s (%d bytes)" % (e.name, e.stat().st_size))

print("\n(READ-ONLY. Tells us whether spark Pressure extends existing machinery or is new.)")
