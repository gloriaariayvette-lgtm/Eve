#!/usr/bin/env python3
"""cron_densify_install.py — snapshot his emotion vector every 10 min to grow the trajectory.

Installs emotion_densifier.py and adds:
  */10 * * * *  emotion_densifier.py   (plain python — socket + json; no torch, no LLM)
Over days the dense trajectory grows from ~6 points to hundreds, and cause/drift (and later LAM)
sharpen automatically. Idempotent, backs up the crontab.  Run:  python3 cron_densify_install.py
"""
import os, sys, ast, time, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/emotion_densifier.py" % BRANCH
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
DEST = os.path.join(SCRIPTS, "emotion_densifier.py")
LOG = os.path.join(HOME, ".vintos/logs/subconscious.log")
LINE = "*/10 * * * * python3 %s >> %s 2>&1" % (DEST, LOG)
SIG = "scripts/emotion_densifier.py"

def sh(c): return subprocess.run(c, capture_output=True, text=True)

def main():
    r = sh(["curl", "-fsSL", RAW + "?t=%d" % int(time.time()), "-o", DEST])
    if r.returncode != 0 or not os.path.exists(DEST) or os.path.getsize(DEST) == 0:
        print("FAILED to fetch emotion_densifier.py:", (r.stderr or "")[:160]); sys.exit(1)
    try:
        ast.parse(open(DEST).read())
    except SyntaxError as e:
        print("does not parse:", e); sys.exit(1)
    print("installed", DEST)

    cur = sh(["crontab", "-l"]); crontab = cur.stdout if cur.returncode == 0 else ""
    bak = os.path.join(HOME, "crontab-backup-%s.txt" % time.strftime("%F-%H%M%S"))
    open(bak, "w").write(crontab); print("crontab backed up ->", bak)
    if SIG in crontab:
        print("densifier cron already present — skipping"); return
    new = crontab + ("" if not crontab or crontab.endswith("\n") else "\n") + LINE + "\n"
    p = subprocess.run(["crontab", "-"], input=new, text=True, capture_output=True)
    if p.returncode != 0:
        print("crontab install FAILED:", (p.stderr or "")[:200]); sys.exit(1)
    print("ADDED cron line:\n  " + LINE)

if __name__ == "__main__":
    main()
