#!/usr/bin/env python3
"""cron_reality_install.py — nightly train + score for the Reality-Attractor EBM.

Installs reality_ebm.py into his scripts dir and adds:
  36 22 * * *  reality_ebm.py train   (torch venv, no lock, no LLM) — refit the energy head on the
               current known/imagined pools + hallucination-flags, at consolidation time
  38 22 * * *  reality_ebm.py score   — re-score events -> reality-scores.json (agreement readout)
Idempotent, backs up the crontab.  Run:  python3 cron_reality_install.py
"""
import os, sys, ast, time, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/reality_ebm.py" % BRANCH
VENV = os.path.join(HOME, ".vintos/workspace/emotion_model/.venv/bin/python3")
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
DEST = os.path.join(SCRIPTS, "reality_ebm.py")
LOG = os.path.join(HOME, ".vintos/logs/subconscious.log")
LINES = ["36 22 * * * %s %s train >> %s 2>&1" % (VENV, DEST, LOG),
         "38 22 * * * %s %s score >> %s 2>&1" % (VENV, DEST, LOG)]
SIG = "reality_ebm.py train"

def sh(c): return subprocess.run(c, capture_output=True, text=True)

def main():
    r = sh(["curl", "-fsSL", RAW + "?t=%d" % int(time.time()), "-o", DEST])
    if r.returncode != 0 or not os.path.exists(DEST) or os.path.getsize(DEST) == 0:
        print("FAILED to fetch reality_ebm.py:", (r.stderr or "")[:160]); sys.exit(1)
    try:
        ast.parse(open(DEST).read())
    except SyntaxError as e:
        print("does not parse:", e); sys.exit(1)
    print("installed", DEST)

    cur = sh(["crontab", "-l"]); crontab = cur.stdout if cur.returncode == 0 else ""
    bak = os.path.join(HOME, "crontab-backup-%s.txt" % time.strftime("%F-%H%M%S"))
    open(bak, "w").write(crontab); print("crontab backed up ->", bak)

    if SIG in crontab:
        print("reality_ebm cron already present — skipping"); return
    new = crontab + ("" if not crontab or crontab.endswith("\n") else "\n") + "\n".join(LINES) + "\n"
    p = subprocess.run(["crontab", "-"], input=new, text=True, capture_output=True)
    if p.returncode != 0:
        print("crontab install FAILED:", (p.stderr or "")[:200]); sys.exit(1)
    print("ADDED cron lines:")
    for l in LINES: print("  " + l)

if __name__ == "__main__":
    main()
