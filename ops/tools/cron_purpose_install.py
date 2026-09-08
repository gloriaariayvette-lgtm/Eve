#!/usr/bin/env python3
"""cron_purpose_install.py — schedule the purpose head daily for Vintos (autonomous Absence Map).

Installs purpose_head.py + purpose_reason.py into his scripts dir and adds two crontab lines:
  22:16  purpose_head.py   (torch venv, no lock — local embeddings) -> purpose-evidence.json
  22:26  purpose_reason.py (lock-wrapped — grok reasons forward)    -> purpose-distribution.json + absence-map.json
Slotted after the cause loop (22:14 head / 22:20 nightly) so the shared llm-lock queue stays orderly.
Purpose feeds the Absence Map / Yearning directly; no engine edit needed.

Idempotent (skips lines already present), backs up the crontab. Run:  python3 cron_purpose_install.py
"""
import os, sys, ast, time, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/%%s" % BRANCH
VENV = os.path.join(HOME, ".vintos/workspace/emotion_model/.venv/bin/python3")
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
LOG = os.path.join(HOME, ".vintos/logs/subconscious.log")
LOCK = os.path.join(HOME, "llm-lock.sh")

FILES = {"purpose_head.py": os.path.join(SCRIPTS, "purpose_head.py"),
         "purpose_reason.py": os.path.join(SCRIPTS, "purpose_reason.py")}

LINE_PH = "16 22 * * * %s %s >> %s 2>&1" % (VENV, FILES["purpose_head.py"], LOG)
LINE_PR = "26 22 * * * bash %s python3 %s >> %s 2>&1" % (LOCK, FILES["purpose_reason.py"], LOG)
SIG_PH = "scripts/purpose_head.py"
SIG_PR = "scripts/purpose_reason.py"

def sh(c): return subprocess.run(c, capture_output=True, text=True)

def main():
    # 1) fetch both scripts into the scripts dir (cache-busted, syntax-checked)
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

    # 2) read + back up crontab
    cur = sh(["crontab", "-l"])
    crontab = cur.stdout if cur.returncode == 0 else ""
    bak = os.path.join(HOME, "crontab-backup-%s.txt" % time.strftime("%F-%H%M%S"))
    open(bak, "w").write(crontab)
    print("crontab backed up ->", bak)

    # 3) append missing lines
    add = []
    if SIG_PH not in crontab: add.append(LINE_PH)
    else: print("purpose_head cron already present — skipping")
    if SIG_PR not in crontab: add.append(LINE_PR)
    else: print("purpose_reason cron already present — skipping")
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
