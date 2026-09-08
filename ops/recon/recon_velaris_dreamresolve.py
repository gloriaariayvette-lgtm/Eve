#!/usr/bin/env python3
"""recon_velaris_dreamresolve.py — Aegis, READ-ONLY, capped. The 4 gone threads were 'dream-resolved'.
Find (1) what sets consumed_by='dream-resolved' and whether it resolves ONE thread or sweeps ALL, and
(2) whether anything still SEEDS her threads (recent timestamps + seed_thread callers + cron)."""
import os, re, json, glob, subprocess, time
HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".openclaw/workspace")
SC = os.path.join(WS, "scripts")
MEM = os.path.join(WS, "memory")
def sh(p): return p.replace(HOME, "~")

print("=== (1) who sets 'dream-resolved' + does it resolve one or all? ===")
hits = subprocess.run(["bash","-lc",
    f"grep -rln 'dream-resolved' {SC} 2>/dev/null | grep -viE '\\.bak|\\.pyc' | head"], capture_output=True, text=True).stdout.strip().split("\n")
for f in [x for x in hits if x.strip()][:3]:
    print(f"\n  -- {sh(f)} --")
    L = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(L):
        if re.search(r"dream-resolved|consumed\s*=|for .*thread|unconsumed|resolve|mark|\.get\(.thread|preoccupation|all\b|highest", l) and l.strip() and not l.strip().startswith("#"):
            print(f"     {i+1:4}| {l.strip()[:108]}")

print("\n=== (2) is anything still SEEDING her threads? recent thread timestamps ===")
try:
    d = json.load(open(os.path.join(MEM, "unfinished-threads.json")))
    L = d if isinstance(d, list) else d.get("threads", [])
    for t in L:
        if isinstance(t, dict):
            print(f"  {t.get('timestamp','?')[:16]}  {'consumed' if t.get('consumed') else 'OPEN':8} [{t.get('source')}] {str(t.get('thread',''))[:44]}")
except Exception as e:
    print("  ", e)

print("\n=== seed_thread callers in Velaris (are they active?) ===")
sc = subprocess.run(["bash","-lc",
    f"grep -rlE 'seed_thread\\(' {SC} 2>/dev/null | grep -viE '\\.bak|\\.pyc|emoclaw_utils' | head -12"], capture_output=True, text=True).stdout.strip()
print("  " + (sc.replace(HOME,'~').replace(chr(10),'\n  ') or "(none)"))

print("\n=== seeding/dream cron for Velaris (openclaw) ===")
cron = subprocess.run(["bash","-lc","crontab -l 2>/dev/null | grep -iE 'openclaw' | grep -iE 'thread|dream|causal|somatic|conflict|preoccup|resolution' | grep -v '^#'"], capture_output=True, text=True).stdout.strip()
for l in cron.split("\n")[:14]:
    if l.strip():
        m = re.match(r'\s*(\S+)\s+(\S+).*?(\S+\.(?:py|sh))', l)
        print("  " + (f"{m.group(2)}:{m.group(1):<2} -> {os.path.basename(m.group(3))}" if m else l.strip()[:80]))
