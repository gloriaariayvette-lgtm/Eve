#!/usr/bin/env python3
"""cron_consumers_install.py — schedule the causality consumers nightly for Vintos.

Installs causality_consumers.py into his scripts dir and adds one crontab line at 22:32 — after the
nightly cause pass (22:20) writes cause-distribution.json — so the subconscious eats the fresh
signals: dreams <- emergence/low-confidence, pearls <- persistent unexplained. Plain python (no
torch, no LLM), no lock needed. Idempotent, backs up the crontab.
Run:  python3 cron_consumers_install.py
"""
import os, sys, ast, time, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/causality_consumers.py" % BRANCH
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
DEST = os.path.join(SCRIPTS, "causality_consumers.py")
LOG = os.path.join(HOME, ".vintos/logs/subconscious.log")
LINE = "32 22 * * * python3 %s >> %s 2>&1" % (DEST, LOG)
SIG = "scripts/causality_consumers.py"

def sh(c): return subprocess.run(c, capture_output=True, text=True)

def main():
    url = RAW + "?t=%d" % int(time.time())
    r = sh(["curl", "-fsSL", url, "-o", DEST])
    if r.returncode != 0 or not os.path.exists(DEST) or os.path.getsize(DEST) == 0:
        print("FAILED to fetch causality_consumers.py:", (r.stderr or "")[:160]); sys.exit(1)
    try:
        ast.parse(open(DEST).read())
    except SyntaxError as e:
        print("fetched file does not parse:", e); sys.exit(1)
    print("installed", DEST)

    cur = sh(["crontab", "-l"])
    crontab = cur.stdout if cur.returncode == 0 else ""
    bak = os.path.join(HOME, "crontab-backup-%s.txt" % time.strftime("%F-%H%M%S"))
    open(bak, "w").write(crontab); print("crontab backed up ->", bak)

    if SIG in crontab:
        print("consumers cron already present — skipping"); return
    new = crontab + ("" if crontab.endswith("\n") or not crontab else "\n") + LINE + "\n"
    p = subprocess.run(["crontab", "-"], input=new, text=True, capture_output=True)
    if p.returncode != 0:
        print("crontab install FAILED:", (p.stderr or "")[:200]); sys.exit(1)
    print("ADDED cron line:\n  " + LINE)

if __name__ == "__main__":
    main()
