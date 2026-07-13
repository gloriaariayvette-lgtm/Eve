#!/usr/bin/env python3
"""cron_sparks_install.py — install + schedule the remaining spark organs for Vintos.

Installs self_pressure, lam, latent_diffuser, graph_mae, tcn, hypergraph into his scripts dir and
schedules them, staggered after the nightly causality cascade:
  22:42 self_pressure       (grok, lock)         — what he composed over
  22:44 lam train           (torch)              — the physics of his interior
  22:46 graph_mae           (torch)              — structural blind spots
  22:48 tcn                 (torch)              — growth vs repetition
  22:50 hypergraph          (torch)              — the relational field
  23:00 latent_diffuser     (torch + grok, lock) — resolve the day's noise into a dream (runs LAST)
Idempotent, backs up the crontab.  Run:  python3 cron_sparks_install.py
"""
import os, sys, ast, time, subprocess

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/%%s" % BRANCH
VENV = os.path.join(HOME, ".vintos/workspace/emotion_model/.venv/bin/python3")
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
LOG = os.path.join(HOME, ".vintos/logs/subconscious.log")
LOCK = os.path.join(HOME, "llm-lock.sh")

def sp(n): return os.path.join(SCRIPTS, n)
FILES = ["self_pressure.py", "lam.py", "latent_diffuser.py", "graph_mae.py", "tcn.py", "hypergraph.py"]
JOBS = [
    ("42 22 * * *", "bash %s python3 %s" % (LOCK, sp("self_pressure.py"))),
    ("44 22 * * *", "%s %s train" % (VENV, sp("lam.py"))),
    ("46 22 * * *", "%s %s" % (VENV, sp("graph_mae.py"))),
    ("48 22 * * *", "%s %s" % (VENV, sp("tcn.py"))),
    ("50 22 * * *", "%s %s" % (VENV, sp("hypergraph.py"))),
    ("0 23 * * *",  "bash %s %s %s" % (LOCK, VENV, sp("latent_diffuser.py"))),
]

def sh(c): return subprocess.run(c, capture_output=True, text=True)

def main():
    for name in FILES:
        dest = sp(name)
        r = sh(["curl", "-fsSL", (RAW % name) + "?t=%d" % int(time.time()), "-o", dest])
        if r.returncode != 0 or not os.path.exists(dest) or os.path.getsize(dest) == 0:
            print("FAILED to fetch", name, (r.stderr or "")[:140]); sys.exit(1)
        try:
            ast.parse(open(dest).read())
        except SyntaxError as e:
            print(name, "does not parse:", e); sys.exit(1)
        print("installed", dest)

    cur = sh(["crontab", "-l"]); crontab = cur.stdout if cur.returncode == 0 else ""
    bak = os.path.join(HOME, "crontab-backup-%s.txt" % time.strftime("%F-%H%M%S"))
    open(bak, "w").write(crontab); print("crontab backed up ->", bak)

    add = []
    for sched, cmd in JOBS:
        line = "%s %s >> %s 2>&1" % (sched, cmd, LOG)
        sig = cmd.split()[-1] if not cmd.startswith("bash") else cmd.split()[-1]  # the script path
        if sig in crontab:
            print("cron already present:", os.path.basename(sig)); continue
        add.append(line)
    if not add:
        print("all spark crons already present."); return
    new = crontab + ("" if not crontab or crontab.endswith("\n") else "\n") + "\n".join(add) + "\n"
    p = subprocess.run(["crontab", "-"], input=new, text=True, capture_output=True)
    if p.returncode != 0:
        print("crontab install FAILED:", (p.stderr or "")[:200]); sys.exit(1)
    print("ADDED %d cron line(s):" % len(add))
    for l in add: print("  " + l)

if __name__ == "__main__":
    main()
