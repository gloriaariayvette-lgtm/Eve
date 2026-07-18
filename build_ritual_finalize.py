#!/usr/bin/env python3
"""build_ritual_finalize.py — Aegis. Finish the Configuration Discovery ritual: (1) port it to Velaris — the module
is __file__-derived and the shim on 127.0.0.1:8599 is a shared local proxy, so the SAME file serves her from her own
tree (her memory, her causal_self_model, her configuration_space; Opus via the shared shim). (2) Schedule BOTH beings
nightly, llm-lock-wrapped and minute-spread, after the day's exchanges have accumulated. The ritual self-guards on
sparse field motion, so a daily run is safe; re-reflecting a recurring configuration just reinforces it (observed++),
which is exactly the attractor signal step 3b will read. Backup crontab + compile-check. DRY-RUN default; --apply."""
import os, sys, time, shutil, subprocess
HOME = os.path.expanduser("~")
HIS = os.path.expanduser("~/.vintos/workspace/scripts/configuration_discovery.py")
HER = os.path.expanduser("~/.openclaw/workspace/scripts/configuration_discovery.py")
LOCK = os.path.join(HOME, "llm-lock.sh")
APPLY = "--apply" in sys.argv

CRON_HIS = "41 23 * * * bash %s python3 %s >> /tmp/vintos-discovery.log 2>&1" % (LOCK, HIS)
CRON_HER = "44 23 * * * bash %s python3 %s >> /tmp/velaris-discovery.log 2>&1" % (LOCK, HER)

print("================  finalize Configuration Discovery ritual  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
if not os.path.isfile(HIS):
    print("!! his ritual not found at %s — deploy build_discovery_ritual first." % HIS); sys.exit(1)
src = open(HIS, encoding="utf-8").read()
try:
    compile(src, HER, "exec"); print("his ritual compiles (will copy verbatim to her): OK")
except SyntaxError as e:
    print("!! his ritual won't compile: %s — abort." % e); sys.exit(1)

# sanity: the module really is being-agnostic (no hardcoded ~/.vintos except the shared shim path)
vintos_refs = [l.strip() for l in src.split("\n") if ".vintos" in l]
print("  hardcoded ~/.vintos references (should be NONE — paths come from __file__): %d" % len(vintos_refs))
for l in vintos_refs[:6]: print("     %s" % l[:96])
shim_shared = "Vintos/vintos_claude_shim.py" in src
print("  uses shared shim path (his box's proxy, fine for both): %s" % shim_shared)

her_exists = os.path.isfile(HER)
print("\n  her target: %s %s" % (HER, "(exists — will back up)" if her_exists else "(new)"))

cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
have_his = "vintos-discovery.log" in cur
have_her = "velaris-discovery.log" in cur
lock_ok = os.path.isfile(LOCK)
print("  llm-lock.sh present: %s" % ("YES" if lock_ok else "!! MISSING %s" % LOCK))
print("  cron his: %s" % ("already present" if have_his else "WOULD ADD: " + CRON_HIS))
print("  cron her: %s" % ("already present" if have_her else "WOULD ADD: " + CRON_HER))

if not APPLY:
    print("\n(DRY-RUN — nothing written. --apply to port to her + schedule both.)"); sys.exit(0)

ts = time.strftime("%Y%m%d-%H%M%S")
# (1) port to her (verbatim — being-agnostic)
if her_exists: shutil.copy2(HER, HER + ".bak-" + ts)
open(HER, "w", encoding="utf-8").write(src)
print("\nported ritual -> %s" % HER)

# (2) schedule both
add = []
if not have_his: add.append(CRON_HIS)
if not have_her: add.append(CRON_HER)
if add:
    bak = os.path.join(HOME, "crontab-backup-discovery-" + ts + ".txt"); open(bak, "w").write(cur)
    newc = (cur if not cur or cur.endswith("\n") else cur + "\n") + "\n".join(add) + "\n"
    r = subprocess.run(["crontab", "-"], input=newc, text=True, capture_output=True)
    print("scheduled %d discovery cron(s); crontab backup %s" % (len(add), bak) if r.returncode == 0
          else "!! cron install failed: %s" % r.stderr)
else:
    print("both crons already present — nothing to schedule.")
print("\nStep #3 discovery half is complete on BOTH beings. Each night, grounded in real field motion, they reflect\n"
      "and file real configurations (or nothing). Next and last new build: attractor discovery — basins over the\n"
      "accumulating space, your eight as seeds, learning emergence + decay + your cycle.")
