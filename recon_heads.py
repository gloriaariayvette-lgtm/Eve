#!/usr/bin/env python3
"""recon_heads.py — Aegis, READ-ONLY. Understand the JEPA head architecture so the missing relational + withheld
heads get built to match. Dumps: (A) jepa_predictor.py in full (its head roster + output schema in jepa-prediction
.json), (B) drift_head.py in full as the head TEMPLATE (how an existing head reads JEPA + produces its signal +
writes/feeds), (C) how heads are scheduled (crontab) and consumed (who reads drift/cause head outputs). Nothing changed."""
import os, re, subprocess, glob
HOME = os.path.expanduser("~")
SCR = os.path.expanduser("~/.vintos/workspace/scripts")
V = os.path.join(HOME, "Vintos")

def dump(name, full=True, grep=None):
    for base in (SCR, V):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
            print(f"----- {p}  ({len(L)}L) -----")
            for i, l in enumerate(L):
                if full or (grep and grep.search(l)):
                    print(f"{i+1:>3}: {l}")
            return p
    print(f"  {name} NOT FOUND"); return None

print("===== (A) jepa_predictor.py (full — head roster + output schema) =====")
dump("jepa_predictor.py")

print("\n===== (B) drift_head.py (full — the head template) =====")
dump("drift_head.py")

print("\n===== (C) head scheduling (crontab) =====")
cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
for l in cron.split("\n"):
    if re.search(r'_head\.py|jepa_predictor|drift_head|cause_head|purpose_head', l) and not l.strip().startswith("#"):
        print(f"  {l.strip()[:100]}")

print("\n===== (C2) who consumes head outputs (drift/relational/withheld signals) =====")
rx = re.compile(r'drift_head|cause_head|purpose_head|relational_head|withheld_head|drift-bias|BEHAVIORAL DRIFT|get_drift', re.I)
for base in (SCR, V):
    for p in glob.glob(base + "/*.py"):
        b = os.path.basename(p)
        if b.endswith("_head.py"): continue
        for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
            if rx.search(l):
                print(f"  {b}:{i+1}: {l.strip()[:92]}")
                break
