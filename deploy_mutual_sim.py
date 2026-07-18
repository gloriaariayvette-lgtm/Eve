#!/usr/bin/env python3
"""deploy_mutual_sim.py — Aegis. Finalize Mutual Simulation: (1) schedule Vintos's cron, (2) give Velaris her own
copy (WS repointed to ~/.openclaw so it optimizes on HER presence-audit history), wire get_interaction_hint into her
subconscious_context, schedule her cron (offset). DRY-RUN default; --apply commits (backups, compile-checks)."""
import os, sys, re, subprocess, time, shutil

APPLY = "--apply" in sys.argv
HOME = os.path.expanduser("~")
HIS = HOME + "/.vintos/workspace/scripts"
HER = HOME + "/.openclaw/workspace/scripts"
SUBCON = HER + "/subconscious_context.py"

print("================  deploy mutual simulation  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))

his = os.path.join(HIS, "mutual_simulation.py")
if not os.path.isfile(his):
    print("!! his mutual_simulation.py not found — apply the build first"); sys.exit(1)
txt = open(his, encoding="utf-8", errors="ignore").read()
n = txt.count('"~/.vintos/workspace"))')
her_src = txt.replace('"~/.vintos/workspace"))', '"~/.openclaw/workspace"))')
try: compile(her_src, HER + "/mutual_simulation.py", "exec"); ok = "OK"
except SyntaxError as e: ok = "ERR %s" % e
print("her mutual_simulation.py: WS anchor x%d -> openclaw (compiles=%s); openclaw=%d vintos-left=%d" %
      (n, ok, her_src.count('"~/.openclaw/workspace"))'), her_src.count('"~/.vintos/workspace"))')))

WIRE = ('    try:  # mutual simulation — the interaction model, optimized by presence scores\n'
        '        from mutual_simulation import get_interaction_hint as _mib\n'
        '        _mi = _mib()\n'
        '        if _mi: parts.append(_mi)\n'
        '    except Exception: pass\n')
ANCHOR = '    if not parts:\n        return ""'
sub = open(SUBCON, encoding="utf-8", errors="ignore").read() if os.path.isfile(SUBCON) else None
sub_new = None
if sub and "mutual_simulation" in sub:
    print("subconscious_context: already wired — skip")
elif sub and sub.count(ANCHOR) == 1:
    sub_new = sub.replace(ANCHOR, WIRE + "\n" + ANCHOR, 1)
    try: compile(sub_new, SUBCON, "exec"); print("subconscious_context: interaction hint would wire (compiles OK)")
    except SyntaxError as e: print("!! subcon err: %s" % e); sub_new = None
else:
    print("!! subconscious_context anchor not unique/found")

cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
HIS_CRON = "26 1,7,13,19 * * * SPARK_WORKSPACE=%s/.vintos/workspace /usr/bin/python3 %s/mutual_simulation.py >> /tmp/mutual-sim.log 2>&1" % (HOME, HIS)
HER_CRON = "36 1,7,13,19 * * * SPARK_WORKSPACE=%s/.openclaw/workspace /usr/bin/python3 %s/mutual_simulation.py >> /tmp/velaris-mutual-sim.log 2>&1" % (HOME, HER)
add = []
if "/tmp/mutual-sim.log" not in cur: add.append(HIS_CRON)
if "/tmp/velaris-mutual-sim.log" not in cur: add.append(HER_CRON)
print("\ncron to add: %d" % len(add))
for ln in add: print("  " + ln)

if not APPLY:
    print("\n(DRY-RUN — nothing written.)"); sys.exit(0)

ts = time.strftime("%Y%m%d-%H%M%S")
dst = HER + "/mutual_simulation.py"
if os.path.isfile(dst): shutil.copy2(dst, dst + ".bak-" + ts)
open(dst, "w", encoding="utf-8").write(her_src); print("\nwrote %s" % dst)
if sub_new:
    shutil.copy2(SUBCON, SUBCON + ".bak-" + ts); open(SUBCON, "w", encoding="utf-8").write(sub_new); print("wired %s" % SUBCON)
if add:
    bak = HOME + "/crontab-backup-mutualsim-" + ts + ".txt"; open(bak, "w").write(cur)
    newc = (cur if not cur or cur.endswith("\n") else cur + "\n") + "\n".join(add) + "\n"
    p = subprocess.run(["crontab", "-"], input=newc, text=True, capture_output=True)
    print(("scheduled %d cron(s); backup %s" % (len(add), bak)) if p.returncode == 0 else ("!! cron failed: %s" % p.stderr))
print("\nDone. Mutual Simulation live for both beings (his :26, hers :36). Spark list complete pending Inviolables check.")
