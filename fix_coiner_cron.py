#!/usr/bin/env python3
"""fix_coiner_cron.py — schedule Vintos's velqan-coiner (the only step that errored on the input= bug).
Mirrors Velaris's cadence. Backup crontab. Aegis."""
import os, re, time, subprocess
HOME = os.path.expanduser("~")
TC = os.path.expanduser("~/.vintos/workspace/scripts/velqan-coiner.py")

cur = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
if "/.vintos/workspace/scripts/velqan-coiner.py" in cur:
    print("already scheduled:")
    for l in cur.split("\n"):
        if "velqan-coiner" in l and ".vintos" in l: print("  " + l)
    raise SystemExit(0)

vela = next((l for l in cur.split("\n") if "velqan-coiner" in l and "openclaw" in l and not l.strip().startswith("#")), None)
m = re.match(r'^\s*([\d\*][\d\*,/ -]*?)\s+\S', vela) if vela else None
sched = m.group(1) if m else "30 5 * * 0"   # weekly Sunday 05:30 fallback
line = f"{sched} bash {HOME}/llm-lock.sh python3 {TC} >> {HOME}/.vintos/logs/velqan.log 2>&1"

open(os.path.expanduser("~/crontab-backup-%s.txt" % time.strftime("%F-%H%M")), "w").write(cur)
subprocess.run(["bash","-lc","crontab -"], input=cur.rstrip("\n") + "\n" + line + "\n", text=True)
print("added Vintos coiner cron (cadence mirrors Velaris'" + ("s" if vela else " — fallback weekly") + "):")
print("  " + line)
print("\nverify:", subprocess.run(["bash","-lc","crontab -l | grep velqan-coiner"], capture_output=True, text=True).stdout.strip())
