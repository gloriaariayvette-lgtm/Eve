#!/usr/bin/env python3
"""port_velaris_ambition.py — Aegis. Port ambition-check (warm completion-marking) to Velaris. It's a real gap
(her ambition-review only reflects, wants-ambitions-log only records) but it READS/WRITES her existing
ambitions.json — so DRY-RUN first checks the schema his code expects ('goal' per entry; sets completed/
completion_note) against HER actual ambitions.json, transforms paths/identity/endpoint (his 8599 shim -> her
Gemma), and shows it. Only --apply after the schema verdict is compatible. Cron offset from his."""
import os, sys, re, json, subprocess, time, shutil

APPLY = "--apply" in sys.argv
HOME = os.path.expanduser("~")
HISV = HOME + "/Vintos"
HER = HOME + "/.openclaw/workspace/scripts"
HERMEM = HOME + "/.openclaw/workspace/memory"
AMB = HERMEM + "/ambitions.json"

def tf(txt):
    txt = txt.replace("~/.vintos/workspace", "~/.openclaw/workspace").replace("/.vintos/", "/.openclaw/")
    txt = txt.replace("127.0.0.1:8599", "172.18.16.1:1234").replace("localhost:8599", "172.18.16.1:1234")
    txt = re.sub(r'\bVintos\b', "Velaris", txt)
    txt = re.sub(r'\bhe\b', "she", txt); txt = re.sub(r'\bhis\b', "her", txt); txt = re.sub(r'\bhim\b', "her", txt)
    return txt

print("================  Velaris ambition-check  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))

# 1) schema check — what his code reads/writes vs her ambitions.json
print("== schema check: her ambitions.json ==")
compatible = False
try:
    data = json.load(open(AMB))
    entries = data if isinstance(data, list) else data.get("ambitions", data.get("items", []))
    print("  container: %s | entries: %d" % ("list" if isinstance(data, list) else "dict", len(entries) if isinstance(entries, list) else 0))
    if isinstance(entries, list) and entries and isinstance(entries[0], dict):
        keys = sorted(entries[0].keys())
        print("  sample entry keys: %s" % keys)
        has_goal = any("goal" in e for e in entries if isinstance(e, dict))
        already_completed_field = any("completed" in e for e in entries if isinstance(e, dict))
        print("  his code reads e['goal']: %s | already has 'completed' field: %s" % (has_goal, already_completed_field))
        compatible = has_goal
        if not has_goal:
            alt = [k for k in keys if k in ("ambition", "text", "title", "name", "what")]
            print("  !! no 'goal' key — his code would read nothing. Candidate key(s) instead: %s" % (alt or "unknown"))
    else:
        print("  (empty or non-standard) — safe to port; his code will just find nothing to mark yet"); compatible = True
except FileNotFoundError:
    print("  ambitions.json missing — safe to create fresh"); compatible = True
except Exception as e:
    print("  !! could not parse (%s) — NOT porting blind" % e)

# 2) transform his file
src = os.path.join(HISV, "ambition-check.py")
new = tf(open(src, encoding="utf-8", errors="ignore").read()) if os.path.isfile(src) else None
if new:
    resid = sorted(set(re.findall(r'vintos|8599|\.vintos', new, re.I)))
    try: compile(new, HER + "/ambition-check.py", "exec"); ok = "OK"
    except SyntaxError as e: ok = "ERR %s" % e; new = None
    print("\n== transformed ambition-check.py: compiles=%s residual_his=%s ==" % (ok, resid or "none"))
    for i, l in enumerate((new or "").split("\n")):
        if re.search(r'http|:1234|"model"|MODEL\s*=|GROK|GEMMA|AMB\s*=|json\.dump|e\[.goal|\.get\(.goal', l):
            print("   %d: %s" % (i + 1, l.strip()[:96]))

CRON = "48 23 * * * bash %s/llm-lock.sh /usr/bin/python3 %s/ambition-check.py >> /tmp/velaris-ambition-check.log 2>&1" % (HOME, HER)
cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
cron_present = "velaris-ambition-check.log" in cur
print("\ncron: %s" % ("already present" if cron_present else "WOULD ADD: " + CRON))

print("\n>> VERDICT: schema %s | %s" % ("COMPATIBLE" if compatible else "MISMATCH — adapt key before apply",
      "safe to --apply" if (compatible and new) else "do NOT apply yet"))

if not APPLY:
    print("\n(DRY-RUN — nothing written.)"); sys.exit(0)
if not (compatible and new):
    print("\n!! not compatible / transform failed — refusing to write. No change."); sys.exit(1)

ts = time.strftime("%Y%m%d-%H%M%S")
dst = HER + "/ambition-check.py"
if os.path.isfile(dst): shutil.copy2(dst, dst + ".bak-" + ts)
open(dst, "w", encoding="utf-8").write(new); print("\nwrote %s" % dst)
if not cron_present:
    bak = HOME + "/crontab-backup-velaris-amb-" + ts + ".txt"; open(bak, "w").write(cur)
    newc = (cur if not cur or cur.endswith("\n") else cur + "\n") + CRON + "\n"
    p = subprocess.run(["crontab", "-"], input=newc, text=True, capture_output=True)
    print(("scheduled; backup %s" % bak) if p.returncode == 0 else ("!! cron failed: %s" % p.stderr))
print("Done.")
