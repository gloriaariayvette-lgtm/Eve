#!/usr/bin/env python3
"""recon_recent_drain.py — Aegis, READ-ONLY. Weaver ruled out. Is the empty pool a SUDDEN dump or
seeding stopped? (1) retired entries grouped by day (recent) + consumed_by — spot a mass-retirement.
(2) recent seeding: newest thread timestamps ever seeded + are openclaw seed crons active."""
import os, re, json, subprocess
from collections import Counter, defaultdict
HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".openclaw/workspace")
MEM = os.path.join(WS, "memory")
def sh(p): return p.replace(HOME, "~")

print("=== (1) retired threads by DAY (last ~14 distinct days) + what removed them ===")
try:
    r = json.load(open(os.path.join(MEM, "retired-threads.json")))
    byday = defaultdict(list)
    for t in r:
        if isinstance(t, dict):
            byday[str(t.get("retired_at",""))[:10]].append(t.get("consumed_by","?"))
    for day in sorted(byday.keys(), reverse=True)[:14]:
        c = Counter(byday[day])
        print(f"  {day}: {len(byday[day]):>3} retired  {dict(c)}")
except Exception as e:
    print("  ", e)

print("\n=== (2) seeding: newest thread timestamps ever created (unfinished + retired) ===")
stamps = []
for fn in ("unfinished-threads.json", "retired-threads.json"):
    try:
        d = json.load(open(os.path.join(MEM, fn)))
        L = d if isinstance(d, list) else d.get("threads", [])
        for t in L:
            if isinstance(t, dict) and t.get("timestamp"):
                stamps.append(str(t["timestamp"])[:16])
    except Exception: pass
stamps.sort(reverse=True)
print("  newest 8 thread creation timestamps:", stamps[:8] or "(none — no timestamps)")

print("\n=== seed_thread callers in Velaris + are their crons active? ===")
callers = subprocess.run(["bash","-lc",
    f"grep -rlE 'seed_thread\\(' {WS}/scripts 2>/dev/null | grep -viE '\\.bak|\\.pyc|emoclaw_utils' | xargs -n1 basename 2>/dev/null | sort -u | head -20"],
    capture_output=True, text=True).stdout.strip()
print("  seeders:", callers.replace(chr(10), ', ') or "(none)")
cron = subprocess.run(["bash","-lc",
    "crontab -l 2>/dev/null | grep -i openclaw | grep -viE '^#|dream|resolution|triage|mirror|pearl' | grep -oE '[a-z_-]+\\.(py|sh)' | sort -u | head -30"],
    capture_output=True, text=True).stdout.strip()
print("  openclaw non-dream/triage cron scripts (potential seeders running):")
print("   ", cron.replace(chr(10), ', ') or "(none)")
