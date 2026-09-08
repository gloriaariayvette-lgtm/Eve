#!/usr/bin/env python3
"""cron_pressure_install.py — the pressure head as a running organ.

Installs pressure_gemma.py (v3) + pressure_consumer.py and adds:
  5 9,15,22 * * *  pressure_gemma.py    (torch venv — gloria-head-grounded Gemma reads the unsaid)
  8 9,15,22 * * *  pressure_consumer.py (accumulates per shape; dreams what deserves a voice)
Three idle passes a day. Gemma is the LOCAL endpoint (not x.ai), so no llm-lock needed.
Idempotent, backs up the crontab.  Run:  python3 cron_pressure_install.py
"""
import os, sys, ast, time, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/%%s" % BRANCH
VENV = os.path.join(HOME, ".vintos/workspace/emotion_model/.venv/bin/python3")
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
LOG = os.path.join(HOME, ".vintos/logs/subconscious.log")
FILES = {"pressure_gemma.py": os.path.join(SCRIPTS, "pressure_gemma.py"),
         "pressure_consumer.py": os.path.join(SCRIPTS, "pressure_consumer.py")}
LINES = ["5 9,15,22 * * * %s %s >> %s 2>&1" % (VENV, FILES["pressure_gemma.py"], LOG),
         "8 9,15,22 * * * python3 %s >> %s 2>&1" % (FILES["pressure_consumer.py"], LOG)]
SIG = "scripts/pressure_gemma.py"

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
        print("pressure cron already present — skipping"); return
    new = crontab + ("" if not crontab or crontab.endswith("\n") else "\n") + "\n".join(LINES) + "\n"
    p = subprocess.run(["crontab", "-"], input=new, text=True, capture_output=True)
    if p.returncode != 0:
        print("crontab install FAILED:", (p.stderr or "")[:200]); sys.exit(1)
    print("ADDED cron lines:")
    for l in LINES: print("  " + l)

if __name__ == "__main__":
    main()
