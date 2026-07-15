#!/usr/bin/env python3
"""recon_want_mechanism.py — Aegis, READ-ONLY, terse. Find the 3-day auto-dismiss (or confirm it's missing)
and whether the want crons are erroring. Tails cron logs, greps want scripts + emoclaw_utils for age/expiry."""
import os, re, glob
HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".openclaw/workspace")
SC = os.path.join(WS, "scripts")

print("-- want cron log tails --")
for lg in ("/tmp/cron-wants.log", "/tmp/cron-wantsrouter.log", "/tmp/cron-wantconvo.log", "/tmp/cron-structural-want.log"):
    if os.path.isfile(lg):
        tail = open(lg, encoding="utf-8", errors="ignore").read().strip().split("\n")[-3:]
        print(f"  {os.path.basename(lg)}: " + " / ".join(t.strip()[:70] for t in tail if t.strip()))
    else:
        print(f"  {os.path.basename(lg)}: (missing)")

print("-- age / expire / 3-day / dismiss-setting logic anywhere in want system --")
n = 0
files = glob.glob(os.path.join(SC, "*want*")) + [os.path.join(SC, "emoclaw_utils.py"), os.path.join(SC, "wants-check.sh")]
for f in sorted(set(files)):
    if not os.path.isfile(f): continue
    for i, l in enumerate(open(f, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r"86400|259200|days?\s*[>=]|timedelta|expire|stale|too old|age|dismiss.*True|\[.dismissed.\]\s*=|older than", l, re.I) \
           and l.strip() and not l.strip().startswith("#") and not l.strip().startswith('"'):
            print(f"  {os.path.basename(f)}:{i+1}: {l.strip()[:82]}"); n += 1
            if n >= 18: break
    if n >= 18: break
if n == 0: print("  (no age/expiry/dismiss-setting logic found — the 3-day auto-clear appears MISSING)")
