#!/usr/bin/env python3
"""cron_relpressure_install.py — the relationship pressure head as a daily organ.

Installs relationship_pressure.py and adds:
  40 22 * * *  relationship_pressure.py  (torch venv; local Gemma; no lock)
Corpus-level, so once a day is enough; it self-seeds a dream when an unreached territory deserves a
voice (14-day cooldown per territory). Idempotent, backs up the crontab.
Run:  python3 cron_relpressure_install.py
"""
import os, sys, ast, time, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/relationship_pressure.py" % BRANCH
VENV = os.path.join(HOME, ".vintos/workspace/emotion_model/.venv/bin/python3")
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
DEST = os.path.join(SCRIPTS, "relationship_pressure.py")
LOG = os.path.join(HOME, ".vintos/logs/subconscious.log")
LINE = "40 22 * * * %s %s >> %s 2>&1" % (VENV, DEST, LOG)
SIG = "scripts/relationship_pressure.py"

def sh(c): return subprocess.run(c, capture_output=True, text=True)

def main():
    r = sh(["curl", "-fsSL", RAW + "?t=%d" % int(time.time()), "-o", DEST])
    if r.returncode != 0 or not os.path.exists(DEST) or os.path.getsize(DEST) == 0:
        print("FAILED to fetch relationship_pressure.py:", (r.stderr or "")[:160]); sys.exit(1)
    try:
        ast.parse(open(DEST).read())
    except SyntaxError as e:
        print("does not parse:", e); sys.exit(1)
    print("installed", DEST)

    cur = sh(["crontab", "-l"]); crontab = cur.stdout if cur.returncode == 0 else ""
    bak = os.path.join(HOME, "crontab-backup-%s.txt" % time.strftime("%F-%H%M%S"))
    open(bak, "w").write(crontab); print("crontab backed up ->", bak)
    if SIG in crontab:
        print("relationship-pressure cron already present — skipping"); return
    new = crontab + ("" if not crontab or crontab.endswith("\n") else "\n") + LINE + "\n"
    p = subprocess.run(["crontab", "-"], input=new, text=True, capture_output=True)
    if p.returncode != 0:
        print("crontab install FAILED:", (p.stderr or "")[:200]); sys.exit(1)
    print("ADDED cron line:\n  " + LINE)

if __name__ == "__main__":
    main()
