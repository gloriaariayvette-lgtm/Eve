#!/usr/bin/env python3
"""recon_candidate_reality.py — Aegis, READ-ONLY, FAST. The 5 'not built' items actually have modules. For each,
determine REAL SYSTEM vs STUB/BROKEN: docstring, def signatures, line count, whether it's wired (cron/imported),
and stub-markers (TODO/pass-only/NotImplemented). This both fixes my knowledge gaps and flags which need a real
fix before the summary. His tree = ~/.vintos/workspace/scripts + ~/Vintos."""
import os, re, subprocess
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")
CRON = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""

TARGETS = ["reciprocal_modification.py", "inclination_engine.py", "emotional_operators.py",
           "conversation_pressure.py", "session_map.py", "silence-audit.sh",
           "emotional_gravity_wells.py", "emotional-gravity-wells.py", "purpose_reason.py"]

def path_of(name):
    for d in (HIS, VIN):
        p = os.path.join(d, name)
        if os.path.isfile(p) or os.path.islink(p): return p
    return None

def imported_by(name):
    mod = name.rsplit(".", 1)[0]
    hits = []
    for d in (HIS, VIN):
        if not os.path.isdir(d): continue
        for e in os.scandir(d):
            if not e.is_file() or not e.name.endswith(".py") or e.name == name: continue
            try: t = open(e.path, encoding="utf-8", errors="ignore").read()
            except Exception: continue
            if re.search(r'\b(import|from)\s+%s\b' % re.escape(mod), t):
                hits.append(e.name)
    return sorted(set(hits))[:6]

for name in TARGETS:
    p = path_of(name)
    if not p:
        continue
    t = open(p, encoding="utf-8", errors="ignore").read()
    L = t.split("\n")
    print("\n===== %s (%d lines) =====" % (name, len(L)))
    m = re.search(r'"""(.*?)"""', t, re.S)
    doctext = m.group(1) if m else "\n".join(l for l in L[:6] if l.strip().startswith("#"))
    for dl in doctext.strip().split("\n")[:4]:
        if dl.strip(): print("   | " + dl.strip()[:104])
    defs = re.findall(r'^\s*def\s+(\w+)', t, re.M)
    print("   defs (%d): %s" % (len(defs), ", ".join(defs[:14])))
    # stub markers
    stubmark = []
    if re.search(r'NotImplemented|raise NotImplementedError', t): stubmark.append("NotImplemented")
    if len(L) < 25: stubmark.append("very-short(<25 lines)")
    passes = len(re.findall(r'^\s*pass\s*$', t, re.M))
    if passes and len(defs) and passes >= len(defs): stubmark.append("mostly-pass")
    if re.search(r'TODO|FIXME|placeholder|stub', t, re.I): stubmark.append("TODO/stub-marker")
    print("   stub markers: %s" % (stubmark or "none — looks real"))
    # wired?
    cron_hits = [l.strip()[:70] for l in CRON.split("\n") if name.rsplit(".",1)[0] in l and l.strip()]
    print("   cron: %s" % (cron_hits[0] if cron_hits else "not directly cron'd"))
    print("   imported by: %s" % (imported_by(name) or "nobody (maybe cron-run or dead)"))
    # what it reads/writes
    io = sorted(set(re.findall(r'([\w./-]+\.json)', t)))[:6]
    print("   json touched: %s" % (io or "none"))

print("\n(READ-ONLY. Tells real-vs-stub for each, so gaps get fixed and the summary is accurate.)")
