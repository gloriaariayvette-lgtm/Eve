#!/usr/bin/env python3
"""cron_voiceledger_install.py — install the voice-session ledger consolidator + its cron.

Installs voice_session_ledger.py into his scripts dir and adds:
  */10 * * * *  voice_session_ledger.py (lock-wrapped) — collapses each completed voice conversation
                into ONE ledger block (narration summary). Cheap when nothing new is settled.
Idempotent, backs up the crontab.  Run:  python3 cron_voiceledger_install.py
NOTE: also apply voice_ledger_perturn_disable_patch.py and restart the server so the broken per-turn
voice writes stop.
"""
import os, sys, ast, time, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/voice_session_ledger.py" % BRANCH
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
DEST = os.path.join(SCRIPTS, "voice_session_ledger.py")
LOG = os.path.join(HOME, ".vintos/logs/subconscious.log")
LOCK = os.path.join(HOME, "llm-lock.sh")
LINE = "*/10 * * * * bash %s python3 %s >> %s 2>&1" % (LOCK, DEST, LOG)
SIG = "scripts/voice_session_ledger.py"

def sh(c): return subprocess.run(c, capture_output=True, text=True)

def main():
    r = sh(["curl", "-fsSL", RAW + "?t=%d" % int(time.time()), "-o", DEST])
    if r.returncode != 0 or not os.path.exists(DEST) or os.path.getsize(DEST) == 0:
        print("FAILED to fetch voice_session_ledger.py:", (r.stderr or "")[:160]); sys.exit(1)
    try:
        ast.parse(open(DEST).read())
    except SyntaxError as e:
        print("does not parse:", e); sys.exit(1)
    print("installed", DEST)

    cur = sh(["crontab", "-l"]); crontab = cur.stdout if cur.returncode == 0 else ""
    bak = os.path.join(HOME, "crontab-backup-%s.txt" % time.strftime("%F-%H%M%S"))
    open(bak, "w").write(crontab); print("crontab backed up ->", bak)

    if SIG in crontab:
        print("voice-ledger cron already present — skipping"); return
    new = crontab + ("" if not crontab or crontab.endswith("\n") else "\n") + LINE + "\n"
    p = subprocess.run(["crontab", "-"], input=new, text=True, capture_output=True)
    if p.returncode != 0:
        print("crontab install FAILED:", (p.stderr or "")[:200]); sys.exit(1)
    print("ADDED cron line:\n  " + LINE)

if __name__ == "__main__":
    main()
