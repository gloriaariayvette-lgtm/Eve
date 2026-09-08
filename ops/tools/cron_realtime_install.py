#!/usr/bin/env python3
"""cron_realtime_install.py — signal-gated realtime causality for Vintos.

Refreshes cause_head.py (now CAUSE_SINCE-aware) and installs realtime_causality.py into his scripts
dir, then adds a frequent poll:
  */20 8-23  realtime_causality.py (lock-wrapped) — cheap gate; forms + records a hypothesis only
             when a NEW spike fires, routing it to the subconscious within ~20 min instead of 22:20.
Idempotent, backs up the crontab.  Run:  python3 cron_realtime_install.py
"""
import os, sys, ast, time, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/%%s" % BRANCH
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
LOG = os.path.join(HOME, ".vintos/logs/subconscious.log")
LOCK = os.path.join(HOME, "llm-lock.sh")

FILES = {"cause_head.py": os.path.join(SCRIPTS, "cause_head.py"),
         "realtime_causality.py": os.path.join(SCRIPTS, "realtime_causality.py")}
LINE = "*/20 8-23 * * * bash %s python3 %s >> %s 2>&1" % (LOCK, FILES["realtime_causality.py"], LOG)
SIG = "scripts/realtime_causality.py"

def sh(c): return subprocess.run(c, capture_output=True, text=True)

def main():
    for name, dest in FILES.items():
        r = sh(["curl", "-fsSL", (RAW % name) + "?t=%d" % int(time.time()), "-o", dest])
        if r.returncode != 0 or not os.path.exists(dest) or os.path.getsize(dest) == 0:
            print("FAILED to fetch", name, (r.stderr or "")[:160]); sys.exit(1)
        try:
            ast.parse(open(dest).read())
        except SyntaxError as e:
            print(name, "does not parse:", e); sys.exit(1)
        print("installed", dest)

    cur = sh(["crontab", "-l"]); crontab = cur.stdout if cur.returncode == 0 else ""
    bak = os.path.join(HOME, "crontab-backup-%s.txt" % time.strftime("%F-%H%M%S"))
    open(bak, "w").write(crontab); print("crontab backed up ->", bak)

    if SIG in crontab:
        print("realtime cron already present — skipping (cause_head still refreshed)"); return
    new = crontab + ("" if not crontab or crontab.endswith("\n") else "\n") + LINE + "\n"
    p = subprocess.run(["crontab", "-"], input=new, text=True, capture_output=True)
    if p.returncode != 0:
        print("crontab install FAILED:", (p.stderr or "")[:200]); sys.exit(1)
    print("ADDED cron line:\n  " + LINE)

if __name__ == "__main__":
    main()
