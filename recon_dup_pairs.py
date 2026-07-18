#!/usr/bin/env python3
"""recon_dup_pairs.py — Aegis, READ-ONLY. Inventory hyphen<->underscore twin files (the dead-duplicate landmine).
For each pair (same stem, same extension, -/_ swapped, BOTH present): identical or diverged, and which side is
LIVE (run by cron / imported as a module). This tells us which are safe to symlink now (identical) vs need a
canonical pick first (diverged). Nothing changed."""
import os, re, glob, hashlib, subprocess
HOME = os.path.expanduser("~")
DIRS = [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")]

cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""

def md5(p):
    try: return hashlib.md5(open(p, "rb").read()).hexdigest()
    except Exception: return "?"

# build import corpus (to detect module imports of the underscore name)
allsrc = ""
for d in DIRS:
    for p in glob.glob(d + "/*.py") + glob.glob(d + "/*.sh"):
        try: allsrc += "\n" + open(p, encoding="utf-8", errors="ignore").read()
        except Exception: pass

def live_side(base):
    stem = base.rsplit(".", 1)[0]
    us = stem.replace("-", "_")
    tags = []
    if re.search(r'(^|[ /])' + re.escape(base) + r'(\s|$)', cron): tags.append("cron")
    if re.search(r'\b(import ' + re.escape(us) + r'\b|from ' + re.escape(us) + r' import)', allsrc): tags.append("imported")
    return "+".join(tags) or "-"

for d in DIRS:
    files = {os.path.basename(p) for p in glob.glob(d + "/*.py") + glob.glob(d + "/*.sh")}
    seen = set()
    pairs = []
    for f in sorted(files):
        stem, ext = (f.rsplit(".", 1) + [""])[:2]
        if "-" not in stem and "_" not in stem: continue
        twin_stem = stem.replace("-", "_") if "-" in stem else stem.replace("_", "-")
        twin = twin_stem + "." + ext
        key = tuple(sorted((f, twin)))
        if twin in files and twin != f and key not in seen:
            seen.add(key)
            a, b = os.path.join(d, key[0]), os.path.join(d, key[1])
            pairs.append((key[0], key[1], md5(a) == md5(b), live_side(key[0]), live_side(key[1])))
    ident = [p for p in pairs if p[2]]
    div = [p for p in pairs if not p[2]]
    print("\n===== %s =====" % d)
    print("  twin pairs: %d  (identical: %d, diverged: %d)" % (len(pairs), len(ident), len(div)))
    print("  -- IDENTICAL (safe to symlink dead->live) --")
    for a, b, _, la, lb in ident:
        print("     %-34s [%s]   %-34s [%s]" % (a, la, b, lb))
    print("  -- DIVERGED (need canonical pick first) --")
    for a, b, _, la, lb in div:
        print("     %-34s [%s]   %-34s [%s]" % (a, la, b, lb))
