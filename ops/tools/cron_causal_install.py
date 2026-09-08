#!/usr/bin/env python3
"""cron_causal_install.py — schedule the JEPA causality loop for Vintos (daily, mirrors Velaris).

Installs cause_head.py into his scripts dir and adds two crontab lines:
  22:14  cause_head.py (torch venv, no lock — local embeddings only) -> writes cause-evidence.json
  22:20  causality-engine.py --nightly (lock-wrapped) -> reasons over the evidence, forms + graduates
So evidence is fresh when nightly reasons. Vintos previously had NO nightly run (only main() every
2 days) while Velaris had one — this closes that parity gap too.

Idempotent (skips lines already present), backs up the crontab to ~/crontab-backup-<ts>.txt.
Run:  python3 cron_causal_install.py
"""
import os, sys, ast, time, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/cause_head.py" % BRANCH
VENV = os.path.join(HOME, ".vintos/workspace/emotion_model/.venv/bin/python3")
WS = os.path.join(HOME, ".vintos/workspace")
SCRIPTS = os.path.join(WS, "scripts")
DEST = os.path.join(SCRIPTS, "cause_head.py")
LOG = os.path.join(HOME, ".vintos/logs/subconscious.log")
ENGINE = os.path.join(HOME, "Vintos/causality-engine.py")
LOCK = os.path.join(HOME, "llm-lock.sh")

LINE_HEAD = ("14 22 * * * SPARK_WORKSPACE=%s %s %s >> %s 2>&1" % (WS, VENV, DEST, LOG))
LINE_NIGHT = ("20 22 * * * bash %s python3 %s --nightly >> %s 2>&1" % (LOCK, ENGINE, LOG))
SIG_HEAD = "scripts/cause_head.py"
SIG_NIGHT = "Vintos/causality-engine.py --nightly"

def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def main():
    # 1) place cause_head.py into the scripts dir (cache-busted fetch)
    url = RAW + "?t=%d" % int(time.time())
    r = sh(["curl", "-fsSL", url, "-o", DEST])
    if r.returncode != 0 or not os.path.exists(DEST) or os.path.getsize(DEST) == 0:
        print("FAILED to fetch cause_head.py:", (r.stderr or "")[:200]); sys.exit(1)
    try:
        ast.parse(open(DEST).read())
    except SyntaxError as e:
        print("fetched cause_head.py does not parse:", e); sys.exit(1)
    print("installed", DEST)

    # 2) read current crontab
    cur = sh(["crontab", "-l"])
    crontab = cur.stdout if cur.returncode == 0 else ""

    # 3) back it up
    bak = os.path.join(HOME, "crontab-backup-%s.txt" % time.strftime("%F-%H%M%S"))
    open(bak, "w").write(crontab)
    print("crontab backed up ->", bak)

    # 4) append only the lines that aren't already there
    add = []
    if SIG_HEAD not in crontab: add.append(LINE_HEAD)
    else: print("cause_head cron already present — skipping")
    if SIG_NIGHT not in crontab: add.append(LINE_NIGHT)
    else: print("Vintos --nightly cron already present — skipping")

    if not add:
        print("nothing to add — crontab already has both."); return

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
