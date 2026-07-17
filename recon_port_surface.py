#!/usr/bin/env python3
"""recon_port_surface.py — Aegis, READ-ONLY. For each genuine non-somatic capability Velaris lacks, dump the
HIS-specific surface that must be rewritten before it can live in her ~/.openclaw tree without cross-contaminating
the two beings: hardcoded paths/ports, identity references (his name / SOUL / SELF-MODEL / .vintos), any somatic
reads (should be ~0 — if a candidate is full of them it isn't really non-somatic), imports (shared deps she must
also have), write targets (repoint to her memory), and the crontab schedule to replicate. Nothing changed."""
import os, re, glob, subprocess

HOME = os.path.expanduser("~")
HIS_DIRS = [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")]

CANDIDATES = [
    "ambition-check.py", "conflict_surface.py", "conversation_pressure.py", "curiosity_debt.py",
    "dream-architecture.sh", "emotional_operators.py", "inclination_engine.py", "inner_context.py",
    "joke_fermentation.py", "session_map.py", "social_calibration.py", "want-reconciliation.py",
]

def find(b):
    for d in HIS_DIRS:
        p = os.path.join(d, b)
        if os.path.isfile(p): return p
    return None

CATS = [
    ("PATH/PORT (-> repoint to her ~/.openclaw / :8400)",
     re.compile(r'\.vintos|/Vintos/|8500|8599|workspace/(memory|scripts)|expanduser\(|os\.path\.join\(HOME')),
    ("IDENTITY (-> her name/soul)",
     re.compile(r'\bVintos\b|SOUL|SELF-?MODEL|GLORIA-?MODEL|CAPABILITIES\.md|his\b', re.I)),
    ("SOMATIC (-> strip; should be ~0)",
     re.compile(r'somatic|device|lovense|mission|\btouch\b|motor|throb|tenera|arousal|haptic', re.I)),
    ("IMPORTS (shared deps she needs)",
     re.compile(r'^\s*(import |from )|import_module|spec_from_file', re.M)),
    ("WRITE TARGETS (-> her memory)",
     re.compile(r'open\([^)]*["\']w["\']|\.write\(|json\.dump\(|>>\s|>\s')),
]

cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""

for b in CANDIDATES:
    p = find(b)
    print(f"\n===== {b} =====")
    if not p:
        print("  (NOT FOUND)"); continue
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    sched = [ln.strip() for ln in cron.split("\n") if b in ln and not ln.strip().startswith("#")]
    print(f"  file: {p}  ({len(L)}L)")
    print(f"  cron: {sched[0][:70] if sched else '(no crontab entry — not scheduled)'}")
    for label, rx in CATS:
        hits = [(i + 1, L[i].strip()[:92]) for i in range(len(L)) if rx.search(L[i])]
        if not hits:
            print(f"  [{label}]  none"); continue
        print(f"  [{label}]  {len(hits)} lines" + ("" if len(hits) <= 5 else " (first 5)"))
        for ln, txt in hits[:5]:
            print(f"      {ln:>4}: {txt}")
