#!/usr/bin/env python3
"""patch_danger_reconcile.py — Aegis. (1) Kill the double-poem: remove Vintos's redundant dream-architecture.sh
cron (a bare wrapper duplicating dream_poetry.py's 4:22 run). (2) Symlink the SAFE dead twins in ~/Vintos:
dream-poetry.py -> dream_poetry.py (his cron uses underscore; hyphen dead in his tree), memory-aging.py ->
memory_aging.py (his cron uses underscore; hyphen stale/dead), and the EMPTY 0-byte narrative_identity.py ->
narrative-identity.py (222L). Holds causal-cluster + causality-engine for a separate API-checked unify (imported).
Crontab + files backed up. DRY-RUN default; --apply commits."""
import os, sys, subprocess, time, shutil
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")
APPLY = "--apply" in sys.argv

print("================  danger reconcile  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))

# --- Part 1: remove the redundant dream-architecture cron (his) ---
cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
lines = cron.split("\n")
drop = [l for l in lines if "dream-architecture.sh" in l and "/Vintos/" in l and l.strip() and not l.strip().startswith("#")]
print("== (1) remove redundant poem cron ==")
for l in drop: print("   DROP: " + l.strip()[:110])
if not drop: print("   (no Vintos dream-architecture cron found — already removed?)")
new_cron = "\n".join(l for l in lines if l not in drop)

# --- Part 2: safe dead-twin symlinks in ~/Vintos ---
# (dead_file, canonical_target) — dead becomes a relative symlink -> canonical
SAFE = [
    ("dream-poetry.py", "dream_poetry.py"),
    ("memory-aging.py", "memory_aging.py"),
    ("narrative_identity.py", "narrative-identity.py"),
]
print("\n== (2) safe dead-twin symlinks (in ~/Vintos) ==")
todo = []
for dead, canon in SAFE:
    dp, cp = os.path.join(V, dead), os.path.join(V, canon)
    if os.path.islink(dp):
        print("   %-26s already a symlink — skip" % dead); continue
    if not os.path.isfile(cp):
        print("   %-26s canonical %s MISSING — skip" % (dead, canon)); continue
    dsz = os.path.getsize(dp) if os.path.isfile(dp) else -1
    print("   %-26s (%dB) -> %s (%dB)" % (dead, dsz, canon, os.path.getsize(cp)))
    todo.append((dp, canon))

print("\n== (3) HELD for API-checked unify (imported, diverged) ==")
print("   causal-cluster.py / causal_cluster.py   (underscore imported; hyphen cron+newer)")
print("   causality-engine.py / causality_engine.py (underscore imported; hyphen cron+newer)")
print("   -> next: diff the imported API before unifying, so importers don't break.")

if not APPLY:
    print("\n(DRY-RUN — nothing changed.)"); sys.exit(0)

ts = time.strftime("%Y%m%d-%H%M%S")
if drop:
    open(HOME + "/crontab-backup-poemdedup-" + ts + ".txt", "w").write(cron)
    p = subprocess.run(["crontab", "-"], input=new_cron if new_cron.endswith("\n") else new_cron + "\n", text=True, capture_output=True)
    print("\ncron: %s" % ("removed %d line(s); backup saved" % len(drop) if p.returncode == 0 else "!! failed: " + p.stderr))
for dp, canon in todo:
    try:
        shutil.copy2(dp, dp + ".bak-" + ts)
        os.remove(dp); os.symlink(canon, dp)
        print("linked %s -> %s" % (os.path.basename(dp), canon))
    except Exception as e:
        print("!! %s: %s" % (os.path.basename(dp), e))
print("\nDone. His poems back to one/day; safe twins unified. Two imported pairs held for the API-checked step.")
