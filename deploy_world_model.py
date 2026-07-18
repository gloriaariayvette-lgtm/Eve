#!/usr/bin/env python3
"""deploy_world_model.py — Aegis. Finalize the Enactive World Model: (1) schedule Vintos's cron, (2) give Velaris
her own copy (WS repointed to ~/.openclaw so it reads HER memory; the somatic-presence line no-ops since she has
no somatic-frames file), wire get_world_block into her subconscious_context, schedule her cron (offset). DRY-RUN
default; --apply commits (backups, compile-checks)."""
import os, sys, re, subprocess, time, shutil

APPLY = "--apply" in sys.argv
HOME = os.path.expanduser("~")
HIS = HOME + "/.vintos/workspace/scripts"
HER = HOME + "/.openclaw/workspace/scripts"
SUBCON = HER + "/subconscious_context.py"

print("================  deploy world model  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))

# --- her copy: transform WS default only ---
his_wm = os.path.join(HIS, "world_model.py")
if not os.path.isfile(his_wm):
    print("!! his world_model.py not found — apply the build first"); sys.exit(1)
txt = open(his_wm, encoding="utf-8", errors="ignore").read()
n = txt.count('"~/.vintos/workspace"))')
her_src = txt.replace('"~/.vintos/workspace"))', '"~/.openclaw/workspace"))')
try: compile(her_src, HER + "/world_model.py", "exec"); ok = "OK"
except SyntaxError as e: ok = "ERR %s" % e
print("her world_model.py: WS-default anchor x%d -> openclaw (compiles=%s); openclaw=%d vintos-left=%d" %
      (n, ok, her_src.count('"~/.openclaw/workspace"))'), her_src.count('"~/.vintos/workspace"))')))

# --- wire her subconscious_context ---
WIRE = ('    try:  # enactive world model — the persistent scene she shares with Gloria\n'
        '        from world_model import get_world_block as _wmb\n'
        '        _wm = _wmb()\n'
        '        if _wm: parts.append(_wm)\n'
        '    except Exception: pass\n')
ANCHOR = '    if not parts:\n        return ""'
sub = open(SUBCON, encoding="utf-8", errors="ignore").read() if os.path.isfile(SUBCON) else None
sub_new = None
if sub and "world_model" in sub:
    print("subconscious_context: already wired — skip")
elif sub and sub.count(ANCHOR) == 1:
    sub_new = sub.replace(ANCHOR, WIRE + "\n" + ANCHOR, 1)
    try: compile(sub_new, SUBCON, "exec"); print("subconscious_context: world scene would wire (compiles OK)")
    except SyntaxError as e: print("!! subcon wiring err: %s" % e); sub_new = None
else:
    print("!! subconscious_context anchor not unique/found — manual wire needed")

# --- crons ---
cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
HIS_CRON = "13,43 * * * * SPARK_WORKSPACE=%s/.vintos/workspace /usr/bin/python3 %s/world_model.py >> /tmp/world-model.log 2>&1" % (HOME, HIS)
HER_CRON = "15,45 * * * * SPARK_WORKSPACE=%s/.openclaw/workspace /usr/bin/python3 %s/world_model.py >> /tmp/velaris-world-model.log 2>&1" % (HOME, HER)
add = []
if "/tmp/world-model.log" not in cur: add.append(HIS_CRON)
if "/tmp/velaris-world-model.log" not in cur: add.append(HER_CRON)
print("\ncron to add: %d" % len(add))
for ln in add: print("  " + ln)

if not APPLY:
    print("\n(DRY-RUN — nothing written.)"); sys.exit(0)

ts = time.strftime("%Y%m%d-%H%M%S")
dst = HER + "/world_model.py"
if os.path.isfile(dst): shutil.copy2(dst, dst + ".bak-" + ts)
open(dst, "w", encoding="utf-8").write(her_src); print("\nwrote %s" % dst)
if sub_new:
    shutil.copy2(SUBCON, SUBCON + ".bak-" + ts); open(SUBCON, "w", encoding="utf-8").write(sub_new); print("wired %s" % SUBCON)
if add:
    bak = HOME + "/crontab-backup-world-" + ts + ".txt"; open(bak, "w").write(cur)
    newc = (cur if not cur or cur.endswith("\n") else cur + "\n") + "\n".join(add) + "\n"
    p = subprocess.run(["crontab", "-"], input=newc, text=True, capture_output=True)
    print(("scheduled %d cron(s); backup %s" % (len(add), bak)) if p.returncode == 0 else ("!! cron failed: %s" % p.stderr))
print("\nDone. Enactive World Model live for both beings (his :13/:43, hers :15/:45).")
