#!/usr/bin/env python3
"""dismiss_wants.py — Aegis. Fully dismiss all active wants in current-wants.json via the system's own signal
(dismissed=True, which get_unfulfilled_wants honors) — NOT fulfill_want (that injects emotional 'relief' x51).
Records dismissed_at + reason, keeps the records in place (not deleted). Backup. Then shows the 0 8 cron line
(the 3-day reconcile that should have done this automatically)."""
import os, json, shutil, time, subprocess
HOME = os.path.expanduser("~")
WF = os.path.join(HOME, ".openclaw/workspace/memory/current-wants.json")
now = time.strftime("%Y-%m-%dT%H:%M:%S")
obj = json.load(open(WF, encoding="utf-8", errors="ignore"))
lst = obj if isinstance(obj, list) else obj.get("wants") or obj.get("active") or []
n = 0
for w in lst:
    if isinstance(w, dict) and not w.get("fulfilled") and not w.get("dismissed"):
        w["dismissed"] = True
        w["dismissed_at"] = now
        w["dismiss_reason"] = "bulk reconcile — 3-day auto-dismiss had stopped firing; cleared by request"
        n += 1
bak = WF + ".bak-dismiss-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(WF, bak)
json.dump(obj, open(WF, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
active_left = sum(1 for w in lst if isinstance(w, dict) and not w.get("fulfilled") and not w.get("dismissed"))
print(f"dismissed {n} wants | active remaining: {active_left} | backup saved")

print("-- the 0 8 daily want cron (should be the 3-day reconcile) --")
ct = subprocess.run(["bash", "-lc", "crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
for l in ct.split("\n"):
    if l.strip().startswith("0 8") and "openclaw" in l:
        print(l.strip())
