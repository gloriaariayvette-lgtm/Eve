#!/usr/bin/env python3
"""check_journal_lock.py — Aegis. Is idle-journal actually llm-locked in cron? Terse."""
import subprocess, re
ct = subprocess.run(["bash", "-lc", "crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
lines = [l for l in ct.split("\n") if "idle-journal" in l and not l.strip().startswith("#")]
for l in lines:
    locked = "llm-lock" in l
    print(("LOCKED" if locked else "NOT locked") + ": " + l.strip()[:120])
if not lines:
    print("no idle-journal cron line found")
