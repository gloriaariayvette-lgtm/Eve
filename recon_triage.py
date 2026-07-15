#!/usr/bin/env python3
"""recon_triage.py — Aegis, READ-ONLY, capped. Where is a thread's PULL assigned at triage, so temperature
+ stability can be tagged the SAME way (natively, at entry) instead of a batch recompute?
Dump: seed_thread (writes the thread record), get_salience (the pull weight), and any triage that scores/
assigns priority/salience/pull onto a thread. Show exactly what fields get written onto a thread at birth."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
def sh(p): return p.replace(HOME, "~")

def dump_range(path, a, b, label=""):
    if not os.path.isfile(path):
        print(f"  (missing) {sh(path)}"); return
    lines = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"  -- {sh(path)} {label} --")
    for i in range(a - 1, min(b, len(lines))):
        if lines[i].rstrip():
            print(f"   {i+1:4}| {lines[i][:116]}")

eu = os.path.join(SC, "emoclaw_utils.py")
print("=== seed_thread — the fields written onto a thread at birth ===")
dump_range(eu, 282, 326)

print("\n=== get_salience — how PULL is computed at triage (the pattern to mirror) ===")
dump_range(eu, 48, 90)

print("\n=== who calls seed_thread / assigns priority — the triage entry points ===")
hits = subprocess.run(["bash","-lc",
    f"grep -rnE 'seed_thread\\(|set_preoccupation\\(|\"priority\"|get_salience\\(|triage' "
    f"{SC} 2>/dev/null | grep -viE '\\.bak|\\.pyc|def seed_thread|def set_preoccupation|def get_salience' | head -20"],
    capture_output=True, text=True).stdout.strip()
print("  " + (hits.replace(HOME,'~').replace(chr(10),'\n  ') or "(none)"))

print("\n=== is there a dedicated thread-triage script? ===")
tri = sorted({f for pat in ("*triage*", "*thread*") for f in glob.glob(os.path.join(SC, pat))
              if os.path.isfile(f) and ".bak" not in f and ".pyc" not in f})
for f in tri[:8]:
    print(f"  {sh(f):58} {os.path.getsize(f):>7}B")
