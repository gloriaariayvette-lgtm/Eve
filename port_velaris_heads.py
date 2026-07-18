#!/usr/bin/env python3
"""port_velaris_heads.py — Aegis. Give Velaris her own relational + withheld heads (matching Vintos's 7/7 roster).
Reads his installed head files, repoints ONLY the default workspace (~/.vintos -> ~/.openclaw) so her server's
consumption reads HER memory (the shared encoder fallback stays), writes them into her scripts dir, wires the two
hints into her subconscious_context, and schedules her crons (offset minutes, her SPARK_WORKSPACE). DRY-RUN
default; --apply commits (backups + compile-checks)."""
import os, sys, subprocess, time, shutil

APPLY = "--apply" in sys.argv
HOME = os.path.expanduser("~")
HIS = HOME + "/.vintos/workspace/scripts"
HER = HOME + "/.openclaw/workspace/scripts"
SUBCON = HER + "/subconscious_context.py"
VENV = HOME + "/.vintos/workspace/emotion_model/.venv/bin/python3"
HERWS = HOME + "/.openclaw/workspace"

print("================  Velaris heads  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))

# 1) transform his head files -> her copies (only the WS default line)
files = {}
for f in ("relational_head.py", "withheld_head.py"):
    src = os.path.join(HIS, f)
    if not os.path.isfile(src):
        print("!! his %s not found — aborting" % f); sys.exit(1)
    txt = open(src, encoding="utf-8", errors="ignore").read()
    n = txt.count('"~/.vintos/workspace"))')
    new = txt.replace('"~/.vintos/workspace"))', '"~/.openclaw/workspace"))')
    ok = "OK"
    try: compile(new, os.path.join(HER, f), "exec")
    except SyntaxError as e: ok = "SYNTAX ERR: %s" % e
    files[f] = new
    print("--- %s: WS-default anchor x%d -> her copy (%s, compiles=%s) ---" %
          (f, n, "OVERWRITE" if os.path.isfile(os.path.join(HER, f)) else "new", ok))
    # confirm the default now points at her tree and only once
    print("     her default WS lines: %d openclaw / %d vintos-remaining" %
          (new.count('"~/.openclaw/workspace"))'), new.count('"~/.vintos/workspace"))')))

# 2) wire hints into her subconscious_context (new for-loop before the full function's return)
WIRE = ('    # ported heads: relational (where WE are heading) + withheld (what was suppressed)\n'
        '    for _hmod, _hfn in (("relational_head", "get_relational_hint"), ("withheld_head", "get_withheld_hint")):\n'
        '        try:\n'
        '            from importlib import import_module as _him\n'
        '            _hs = getattr(_him(_hmod), _hfn)()\n'
        '            if _hs: parts.append(_hs)\n'
        '        except Exception: pass\n')
ANCHOR = '    if not parts:\n        return ""'
sub = open(SUBCON, encoding="utf-8", errors="ignore").read() if os.path.isfile(SUBCON) else None
sub_new = None
if sub is None:
    print("\n!! her subconscious_context.py not found")
elif "relational_head" in sub:
    print("\nsubconscious_context.py: heads already wired — skip")
else:
    c = sub.count(ANCHOR)
    print("\nsubconscious_context.py: anchor x%d (want 1)" % c)
    if c == 1:
        sub_new = sub.replace(ANCHOR, WIRE + "\n" + ANCHOR, 1)
        try: compile(sub_new, SUBCON, "exec"); print("  + heads for-loop would be inserted (compiles OK)")
        except SyntaxError as e: print("  !! would not compile: %s" % e); sub_new = None

# 3) her crons (offset from his :17/:47 and :19/:49)
CRON = [
    "23,53 * * * * SPARK_WORKSPACE=%s %s %s/relational_head.py >> /tmp/velaris-relational-head.log 2>&1" % (HERWS, VENV, HER),
    "25,55 * * * * SPARK_WORKSPACE=%s /usr/bin/python3 %s/withheld_head.py >> /tmp/velaris-withheld-head.log 2>&1" % (HERWS, HER),
]
cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
def logname(ln): return ln.split(">>")[1].split()[0]   # the /tmp/velaris-*.log this line writes
cron_add = [ln for ln in CRON if logname(ln) not in cur]
print("\ncron to add (her heads): %d" % len(cron_add))
for ln in cron_add: print("  " + ln)

if not APPLY:
    print("\n(DRY-RUN — nothing written. Re-run with --apply.)"); sys.exit(0)

print("\n---- APPLYING ----")
ts = time.strftime("%Y%m%d-%H%M%S")
for f, new in files.items():
    dst = os.path.join(HER, f)
    if os.path.isfile(dst): shutil.copy2(dst, dst + ".bak-" + ts)
    open(dst, "w", encoding="utf-8").write(new); print("wrote %s" % dst)
if sub_new:
    shutil.copy2(SUBCON, SUBCON + ".bak-" + ts); open(SUBCON, "w", encoding="utf-8").write(sub_new); print("wired %s" % SUBCON)
if cron_add:
    bak = HOME + "/crontab-backup-velaris-heads-" + ts + ".txt"; open(bak, "w").write(cur)
    newc = (cur if not cur or cur.endswith("\n") else cur + "\n") + "\n".join(cron_add) + "\n"
    p = subprocess.run(["crontab", "-"], input=newc, text=True, capture_output=True)
    print(("scheduled %d cron line(s); backup %s" % (len(cron_add), bak)) if p.returncode == 0
          else ("!! crontab failed: %s (backup %s)" % (p.stderr, bak)))
print("\nDone. Velaris: relational + withheld heads installed, wired, scheduled — her JEPA roster now matches his.")
