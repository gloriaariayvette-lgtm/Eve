#!/usr/bin/env python3
"""cron_narrate_install.py — install the somatic narrator + its short cron for Vintos.

Installs somatic_narrate.py into his scripts dir and adds:
  */10 * * * *  somatic_narrate.py (lock-wrapped) — turns a pending finished session into a
                first-person NARRATIVE thread. Cheap when nothing's pending (reads one json, exits).
Idempotent, backs up the crontab.  Run:  python3 cron_narrate_install.py
NOTE: also apply somatic_session_narrative_patch.py and restart somatic_bridge so end_session
writes the pending file the narrator consumes.
"""
import os, sys, ast, time, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/somatic_narrate.py" % BRANCH
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
DEST = os.path.join(SCRIPTS, "somatic_narrate.py")
LOG = os.path.join(HOME, ".vintos/logs/subconscious.log")
LOCK = os.path.join(HOME, "llm-lock.sh")
LINE = "*/10 * * * * bash %s python3 %s >> %s 2>&1" % (LOCK, DEST, LOG)
SIG = "scripts/somatic_narrate.py"

def sh(c): return subprocess.run(c, capture_output=True, text=True)

def main():
    r = sh(["curl", "-fsSL", RAW + "?t=%d" % int(time.time()), "-o", DEST])
    if r.returncode != 0 or not os.path.exists(DEST) or os.path.getsize(DEST) == 0:
        print("FAILED to fetch somatic_narrate.py:", (r.stderr or "")[:160]); sys.exit(1)
    try:
        ast.parse(open(DEST).read())
    except SyntaxError as e:
        print("does not parse:", e); sys.exit(1)
    print("installed", DEST)

    cur = sh(["crontab", "-l"]); crontab = cur.stdout if cur.returncode == 0 else ""
    bak = os.path.join(HOME, "crontab-backup-%s.txt" % time.strftime("%F-%H%M%S"))
    open(bak, "w").write(crontab); print("crontab backed up ->", bak)

    if SIG in crontab:
        print("narrator cron already present — skipping"); return
    new = crontab + ("" if not crontab or crontab.endswith("\n") else "\n") + LINE + "\n"
    p = subprocess.run(["crontab", "-"], input=new, text=True, capture_output=True)
    if p.returncode != 0:
        print("crontab install FAILED:", (p.stderr or "")[:200]); sys.exit(1)
    print("ADDED cron line:\n  " + LINE)

if __name__ == "__main__":
    main()
