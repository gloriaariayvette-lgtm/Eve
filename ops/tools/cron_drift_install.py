#!/usr/bin/env python3
"""cron_drift_install.py — schedule the drift head daily for Vintos (autonomous self-model drift).

Installs drift_head.py + drift_reason.py into his scripts dir and adds two crontab lines:
  22:18  drift_head.py   (torch venv, no lock — embeddings) -> drift.json (geometry + terms)
  22:28  drift_reason.py (lock-wrapped — grok names the move) -> merges characterization into drift.json
Slotted after the cause + purpose loops. mirror-trigger.sh already runs every ~2h on cron and reads
drift.json (Condition 7), so no extra scheduling for the trigger itself.

Idempotent (skips lines already present), backs up the crontab. Run:  python3 cron_drift_install.py
"""
import os, sys, ast, time, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/%%s" % BRANCH
VENV = os.path.join(HOME, ".vintos/workspace/emotion_model/.venv/bin/python3")
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
LOG = os.path.join(HOME, ".vintos/logs/subconscious.log")
LOCK = os.path.join(HOME, "llm-lock.sh")

FILES = {"drift_head.py": os.path.join(SCRIPTS, "drift_head.py"),
         "drift_reason.py": os.path.join(SCRIPTS, "drift_reason.py")}

LINE_DH = "18 22 * * * %s %s >> %s 2>&1" % (VENV, FILES["drift_head.py"], LOG)
LINE_DR = "28 22 * * * bash %s python3 %s >> %s 2>&1" % (LOCK, FILES["drift_reason.py"], LOG)
SIG_DH = "scripts/drift_head.py"
SIG_DR = "scripts/drift_reason.py"

def sh(c): return subprocess.run(c, capture_output=True, text=True)

def main():
    for name, dest in FILES.items():
        url = (RAW % name) + "?t=%d" % int(time.time())
        r = sh(["curl", "-fsSL", url, "-o", dest])
        if r.returncode != 0 or not os.path.exists(dest) or os.path.getsize(dest) == 0:
            print("FAILED to fetch", name, (r.stderr or "")[:160]); sys.exit(1)
        try:
            ast.parse(open(dest).read())
        except SyntaxError as e:
            print("fetched", name, "does not parse:", e); sys.exit(1)
        print("installed", dest)

    cur = sh(["crontab", "-l"])
    crontab = cur.stdout if cur.returncode == 0 else ""
    bak = os.path.join(HOME, "crontab-backup-%s.txt" % time.strftime("%F-%H%M%S"))
    open(bak, "w").write(crontab)
    print("crontab backed up ->", bak)

    add = []
    if SIG_DH not in crontab: add.append(LINE_DH)
    else: print("drift_head cron already present — skipping")
    if SIG_DR not in crontab: add.append(LINE_DR)
    else: print("drift_reason cron already present — skipping")
    if not add:
        print("nothing to add."); return

    new = crontab
    if new and not new.endswith("\n"): new += "\n"
    new += "\n".join(add) + "\n"
    p = subprocess.run(["crontab", "-"], input=new, text=True, capture_output=True)
    if p.returncode != 0:
        print("crontab install FAILED:", (p.stderr or "")[:200]); sys.exit(1)
    print("ADDED %d cron line(s):" % len(add))
    for l in add: print("  " + l)

if __name__ == "__main__":
    main()
