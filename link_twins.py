#!/usr/bin/env python3
"""link_twins.py — Aegis. Collapse hyphen<->underscore twin files to ONE real file + one symlink, killing the
dead-duplicate landmine. CORRECT live-detection: a file is LIVE if it's run by cron, imported as a module
(underscore only — hyphens can't be imported), or exec'd by name (subprocess/Popen/spec_from_file/bash/python3).
Per pair: if exactly one twin is live -> symlink the dead twin to the live one (its divergent content never ran,
so zero behavior change). If both live + identical -> keep underscore real, symlink hyphen to it. If both live +
DIVERGED -> SKIP and report (needs manual reconciliation). Backs up each replaced file; relative symlinks.
DRY-RUN default; --apply commits."""
import os, re, sys, glob, hashlib, subprocess, time, shutil
HOME = os.path.expanduser("~")
DIRS = [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")]
APPLY = "--apply" in sys.argv

cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
corpus = ""
for d in DIRS:
    for p in glob.glob(d + "/*.py") + glob.glob(d + "/*.sh"):
        try: corpus += "\n" + open(p, encoding="utf-8", errors="ignore").read()
        except Exception: pass

def md5(p):
    try: return hashlib.md5(open(p, "rb").read()).hexdigest()
    except Exception: return "?"

EXEC = re.compile(r'(subprocess|Popen|spec_from_file|os\.system|run\(|["\']python3["\']|bash )', re.I)
def is_live(base):
    stem = base.rsplit(".", 1)[0]; us = stem.replace("-", "_")
    if re.search(r'(^|[ /"\'])' + re.escape(base) + r'(\s|$|["\'])', cron): return "cron"
    if "_" in stem and re.search(r'\b(import ' + re.escape(us) + r'\b|from ' + re.escape(us) + r' import)', corpus):
        return "import"
    for line in corpus.split("\n"):
        if base in line and EXEC.search(line): return "exec"
    return ""

total_link, total_skip = [], []
for d in DIRS:
    files = {os.path.basename(p) for p in glob.glob(d + "/*.py") + glob.glob(d + "/*.sh")}
    seen = set()
    print("\n===== %s =====" % d)
    for f in sorted(files):
        stem, ext = (f.rsplit(".", 1) + [""])[:2]
        if "-" not in stem and "_" not in stem: continue
        twin = (stem.replace("-", "_") if "-" in stem else stem.replace("_", "-")) + "." + ext
        key = tuple(sorted((f, twin)))
        if twin not in files or twin == f or key in seen: continue
        seen.add(key)
        hy = key[0] if "-" in key[0].rsplit(".", 1)[0] else key[1]
        us = key[1] if hy == key[0] else key[0]
        hy_p, us_p = os.path.join(d, hy), os.path.join(d, us)
        identical = md5(hy_p) == md5(us_p)
        lh, lu = is_live(hy), is_live(us)
        # decide
        if lh and lu and not identical:
            total_skip.append((d, hy, us, lh, lu)); continue
        if identical:
            real, dead = us, hy  # keep underscore real (import-safe), hyphen -> symlink
        elif lh and not lu:
            real, dead = hy, us
        elif lu and not lh:
            real, dead = us, hy
        elif not lh and not lu:
            real, dead = us, hy  # both dead — collapse anyway
        else:  # both live + identical handled above; both live diverged skipped above
            real, dead = us, hy
        total_link.append((d, dead, real, "identical" if identical else "dead-twin-inert", lh, lu))

print("\n================  PLAN  [%s]  ================" % ("APPLY" if APPLY else "DRY-RUN"))
print("SAFE links: %d   |   DANGER skips (both live + diverged): %d" % (len(total_link), len(total_skip)))
print("\n-- would SYMLINK (dead -> real) --")
for d, dead, real, why, lh, lu in total_link:
    print("   %-32s -> %-30s (%s)" % (dead, real, why))
print("\n-- SKIPPED, need manual reconciliation --")
for d, hy, us, lh, lu in total_skip:
    print("   %-30s [%s]  vs  %-30s [%s]" % (hy, lh, us, lu))

if not APPLY:
    print("\n(DRY-RUN — nothing moved. --apply to create the symlinks.)"); raise SystemExit(0)

ts = time.strftime("%Y%m%d-%H%M%S")
done = 0
for d, dead, real, why, lh, lu in total_link:
    dp, rp = os.path.join(d, dead), os.path.join(d, real)
    if os.path.islink(dp): continue
    try:
        shutil.copy2(dp, dp + ".bak-" + ts)
        os.remove(dp)
        os.symlink(real, dp)   # relative symlink within the dir
        done += 1
    except Exception as e:
        print("  !! %s: %s" % (dead, e))
print("\nlinked %d twins (each dead file backed up to .bak-%s). %d danger pairs left for manual review." % (done, ts, len(total_skip)))
