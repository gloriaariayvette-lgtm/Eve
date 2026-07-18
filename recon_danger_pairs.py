#!/usr/bin/env python3
"""recon_danger_pairs.py — Aegis, READ-ONLY. The 5 both-live diverged twin pairs. For each: both files' size/
mtime/linecount in each dir, the crontab line(s) that run each variant (the double-schedule causing 2 poems etc.),
and which underscore is imported. So we can pick the canonical version, unify (symlink), and drop the duplicate
cron line. Nothing changed."""
import os, re, glob, subprocess, time
HOME = os.path.expanduser("~")
DIRS = [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")]
PAIRS = ["causal-cluster", "causality-engine", "dream-poetry", "memory-aging", "narrative-identity"]

cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
corpus = ""
for d in DIRS:
    for p in glob.glob(d + "/*.py"):
        try: corpus += "\n" + open(p, encoding="utf-8", errors="ignore").read()
        except Exception: pass

def stat(p):
    if os.path.islink(p): return "SYMLINK -> " + os.readlink(p)
    if not os.path.isfile(p): return "absent"
    t = open(p, encoding="utf-8", errors="ignore").read()
    age = (time.time() - os.path.getmtime(p)) / 86400.0
    return "%dL  %dB  mtime %.1fd ago" % (len(t.splitlines()), os.path.getsize(p), age)

for stem in PAIRS:
    hy, us = stem + ".py", stem.replace("-", "_") + ".py"
    usmod = stem.replace("-", "_")
    print("\n===== %s =====" % stem)
    for d in DIRS:
        print("  [%s]" % d)
        print("    %-26s %s" % (hy, stat(os.path.join(d, hy))))
        print("    %-26s %s" % (us, stat(os.path.join(d, us))))
    print("  imported as '%s': %s" % (usmod, "yes" if re.search(r'\b(import ' + usmod + r'\b|from ' + usmod + r' import)', corpus) else "no"))
    print("  crontab lines:")
    for l in cron.split("\n"):
        if (hy in l or us in l) and l.strip() and not l.strip().startswith("#"):
            print("    | " + l.strip()[:118])
