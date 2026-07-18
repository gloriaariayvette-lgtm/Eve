#!/usr/bin/env python3
"""port_velaris_reconciliation.py — Aegis. Velaris has NO want-reconciliation (0 evolved wants) — her wants never
get marked-fulfilled-from-evidence or mutated forward. Port his want-reconciliation.py to her: transform paths ->
~/.openclaw, endpoint (his 8599 shim -> her Gemma) AND the evolve model (grok -> her Gemma model), identity ->
Velaris. Write to her scripts + schedule. DRY-RUN prints the transformed endpoint/model lines to verify HER Gemma
before it lands. --apply commits (backup + compile-check + cron)."""
import os, sys, re, subprocess, time, shutil
HOME = os.path.expanduser("~")
HISV = os.path.join(HOME, "Vintos")
HIS_SCR = os.path.expanduser("~/.vintos/workspace/scripts")
HER = os.path.expanduser("~/.openclaw/workspace/scripts")
APPLY = "--apply" in sys.argv

def his_src():
    for d in (HISV, HIS_SCR):
        p = os.path.join(d, "want-reconciliation.py")
        if os.path.isfile(p) or os.path.islink(p): return p
    return None

def tf(txt):
    txt = txt.replace("~/.vintos/workspace", "~/.openclaw/workspace").replace("/.vintos/", "/.openclaw/")
    txt = txt.replace("127.0.0.1:8599", "172.18.16.1:1234").replace("localhost:8599", "172.18.16.1:1234")
    txt = txt.replace("grok-4.20-0309-non-reasoning", "google/gemma-4-12b-qat")   # evolve runs on her Gemma
    txt = re.sub(r'\bVintos\b', "Velaris", txt)
    txt = re.sub(r'\bhe\b', "she", txt); txt = re.sub(r'\bhis\b', "her", txt); txt = re.sub(r'\bhim\b', "her", txt)
    return txt

src = his_src()
print("================  Velaris want-reconciliation  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
if not src:
    print("!! his want-reconciliation.py not found"); sys.exit(1)
new = tf(open(src, encoding="utf-8", errors="ignore").read())
resid = sorted(set(re.findall(r'vintos|8599|\.vintos|grok', new, re.I)))
try: compile(new, HER + "/want-reconciliation.py", "exec"); ok = "OK"
except SyntaxError as e: ok = "ERR %s" % e
print("transformed want-reconciliation.py: compiles=%s  residual_his=%s" % (ok, resid or "none"))
print("  endpoint/model lines (verify -> HER Gemma 172.18.16.1:1234 / gemma model):")
for i, l in enumerate(new.split("\n")):
    if re.search(r'http|:1234|"model"|MODEL\s*=|GEMMA|GROK|requests\.post|express_want|source="evolution"|source=.evolution', l):
        print("   %d: %s" % (i + 1, l.strip()[:96]))

CRON = "18 23 * * * bash %s/llm-lock.sh python3 %s/want-reconciliation.py >> /tmp/velaris-reconcile.log 2>&1" % (HOME, HER)
cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
have = "velaris-reconcile.log" in cur
print("\ncron: %s" % ("already present" if have else "WOULD ADD: " + CRON))

if not APPLY:
    print("\n(DRY-RUN — nothing written. Verify her Gemma endpoint, then --apply.)"); sys.exit(0)
if ok != "OK":
    print("!! transform did not compile — refusing to write."); sys.exit(1)
ts = time.strftime("%Y%m%d-%H%M%S")
dst = HER + "/want-reconciliation.py"
if os.path.isfile(dst): shutil.copy2(dst, dst + ".bak-" + ts)
open(dst, "w", encoding="utf-8").write(new); print("\nwrote %s" % dst)
if not have:
    bak = HOME + "/crontab-backup-velaris-reconcile-" + ts + ".txt"; open(bak, "w").write(cur)
    newc = (cur if not cur or cur.endswith("\n") else cur + "\n") + CRON + "\n"
    p = subprocess.run(["crontab", "-"], input=newc, text=True, capture_output=True)
    print(("scheduled reconcile cron; backup %s" % bak) if p.returncode == 0 else ("!! cron failed: %s" % p.stderr))
print("\nDone. Velaris now reconciles wants from evidence + evolves fulfilled wants forward (source=evolution).")
