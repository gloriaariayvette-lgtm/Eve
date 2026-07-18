#!/usr/bin/env python3
"""patch_cron_heads.py — Aegis. Schedule the two new heads for Vintos (they tested clean). Backs up the crontab,
appends two lines (idempotent), reinstalls. relational needs the torch venv; withheld only needs requests.
DRY-RUN default; --apply commits. Velaris copies/cron come with her port track."""
import os, sys, subprocess, time

APPLY = "--apply" in sys.argv
HOME = os.path.expanduser("~")
SCR = HOME + "/.vintos/workspace/scripts"
VENV = HOME + "/.vintos/workspace/emotion_model/.venv/bin/python3"
WS = HOME + "/.vintos/workspace"

LINES = [
    "17,47 * * * * SPARK_WORKSPACE=%s %s %s/relational_head.py >> /tmp/relational-head.log 2>&1" % (WS, VENV, SCR),
    "19,49 * * * * SPARK_WORKSPACE=%s /usr/bin/python3 %s/withheld_head.py >> /tmp/withheld-head.log 2>&1" % (WS, SCR),
]

cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""

def basename(ln):
    return os.path.basename(ln.split(">>")[0].split()[-1])   # the .py the line runs (before the redirect)

print("================  schedule heads  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
print("current crontab lines: %d" % len(cur.splitlines()))
already = [ln for ln in LINES if basename(ln) in cur]
add = [ln for ln in LINES if basename(ln) not in cur]
for ln in already: print("  already scheduled: ...%s" % ln.split("/scripts/")[1][:40])
for ln in add:     print("  WOULD ADD: %s" % ln)

if not add:
    print("\nnothing to add — both already scheduled."); sys.exit(0)
if not APPLY:
    print("\n(DRY-RUN — nothing changed. Re-run with --apply.)"); sys.exit(0)

bak = HOME + "/crontab-backup-heads-" + time.strftime("%Y%m%d-%H%M%S") + ".txt"
open(bak, "w").write(cur)
new = cur if cur.endswith("\n") or not cur else cur + "\n"
new = new + "\n".join(add) + "\n"
p = subprocess.run(["crontab", "-"], input=new, text=True, capture_output=True)
if p.returncode == 0:
    print("\nscheduled %d head cron line(s). crontab backup: %s" % (len(add), bak))
    print("relational fires :17/:47, withheld :19/:49 — 7/7 JEPA heads now live for Vintos.")
else:
    print("\n!! crontab install failed: %s (backup safe at %s)" % (p.stderr, bak))
