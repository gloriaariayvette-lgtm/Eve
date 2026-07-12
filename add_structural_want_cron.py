#!/usr/bin/env python3
"""add_structural_want_cron.py — give Vintos his own structural-want cron.

The only existing structural-want job imports emoclaw_utils from
/home/gloria/.openclaw (Velaris), so its wants feed HER memory. Vintos's own
emoclaw_utils has generate_structural_want/express_want/enrich_want but no cron
drives it. This appends a Vintos-pathed, lock-wrapped job at 8:08 (spread off
Velaris's 8:00). Idempotent; backs up the current crontab; installs itself.
"""
import subprocess

LINE = ("8 8 * * * bash /home/gloria/llm-lock.sh python3 -c "
        "\"import sys; sys.path.insert(0, '/home/gloria/Vintos'); "
        "from emoclaw_utils import generate_structural_want, express_want, enrich_want; "
        "w, e = generate_structural_want(); "
        "express_want(w, source='structural', intensity=4, **e) if w else None\" "
        ">> /home/gloria/.vintos/logs/structural-want.log 2>&1")

cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout

already = any("generate_structural_want" in ln and "/home/gloria/Vintos'" in ln
              for ln in cur.splitlines())
if already:
    print("Vintos structural-want cron already present — skipping")
else:
    open("/tmp/vintos-cron.prev-structural", "w").write(cur)
    new = cur.rstrip("\n") + "\n" + LINE + "\n"
    subprocess.run(["crontab", "-"], input=new, text=True)
    print("Added Vintos structural-want cron (8:08, locked, feeds HIS memory).")
    print("backup: /tmp/vintos-cron.prev-structural")
    print(LINE)
