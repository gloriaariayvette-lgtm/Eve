#!/usr/bin/env python3
"""fix_coiner_cron2.py — schedule Vintos's coiner with the FULL 5-field cron (last attempt grabbed one
field). Weekly, offset from Velaris's Sunday 22:00 slot. Backup crontab. Aegis."""
import os, time, subprocess
HOME = os.path.expanduser("~")
TC = os.path.expanduser("~/.vintos/workspace/scripts/velqan-coiner.py")

cur = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
if "/.vintos/workspace/scripts/velqan-coiner.py" in cur:
    print("already scheduled:", next((l for l in cur.split("\n") if ".vintos" in l and "velqan-coiner" in l), ""))
    raise SystemExit(0)

SCHED = "20 22 * * 0"   # weekly Sunday 22:20 — mirrors her cadence, offset so the lock queue isn't a pile-up
line = f"{SCHED} bash {HOME}/llm-lock.sh python3 {TC} >> {HOME}/.vintos/logs/velqan.log 2>&1"
open(os.path.expanduser("~/crontab-backup-%s.txt" % time.strftime("%F-%H%M")), "w").write(cur)
new = cur.rstrip("\n") + "\n" + line + "\n"
r = subprocess.run(["bash","-lc","crontab -"], input=new, text=True, capture_output=True)
if r.returncode != 0:
    print("!! crontab rejected (unchanged):", r.stderr[:160])
else:
    print("scheduled:", line)
    print("verify:", subprocess.run(["bash","-lc","crontab -l | grep 'vintos.*velqan-coiner'"], capture_output=True, text=True).stdout.strip())
