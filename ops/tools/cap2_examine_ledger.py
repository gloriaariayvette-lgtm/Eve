#!/usr/bin/env python3
"""cap2_examine_ledger.py — Aegis. (1) Cap humor+taste profile reads (head -c, keeps the opening structure).
(2) EXAMINE the interaction ledger: total entries, date range, sort order, and how introspection slices its
'last 20' — to see why March entries surface as 'recent'. Backup + bash -n + re-measure."""
import os, re, json, shutil, time, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
MEM = os.path.join(HOME, ".openclaw/workspace/memory")

# (1) cap profiles
t = open(P, encoding="utf-8", errors="ignore").read()
for old, new in (('cat "$WORKSPACE/memory/humor-profile.json"', 'head -c 4000 "$WORKSPACE/memory/humor-profile.json"'),
                 ('cat "$WORKSPACE/memory/taste-profile.json"', 'head -c 4000 "$WORKSPACE/memory/taste-profile.json"')):
    if new in t: continue
    if t.count(old) == 1: t = t.replace(old, new, 1)
    else: print(f"anchor {old[:30]!r} x{t.count(old)} — skipped")
bak = P + ".bak-cap2-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(t)
c = subprocess.run(["bash", "-n", P], capture_output=True, text=True)
if c.returncode: shutil.copy2(bak, P); print("bash -n failed, reverted"); raise SystemExit(1)
print("capped humor+taste profiles (backup saved)")

# (2) examine ledger
lp = os.path.join(MEM, "interaction-ledger.json")
try:
    L = json.load(open(lp, encoding="utf-8", errors="ignore"))
    ts = [e.get("timestamp", "") for e in L if isinstance(e, dict)]
    ts_sorted = ts == sorted(ts)
    print(f"ledger: {len(L)} entries | first ts={ts[0][:16] if ts else '-'} | last ts={ts[-1][:16] if ts else '-'} | sorted_asc={ts_sorted}")
    print(f"  min ts={min(ts)[:16] if ts else '-'} | max ts={max(ts)[:16] if ts else '-'}")
except Exception as e:
    print("ledger read:", e)

print("-- how introspection builds the 'last 20' ledger --")
for i, l in enumerate(open(P, encoding="utf-8", errors="ignore").read().split("\n")):
    if re.search(r'interaction-ledger|INTERACTION LEDGER|last 20|\[-20:\]|\[:20\]|ledger\[', l) and l.strip():
        print(f"  {i+1}: {l.strip()[:96]}")

# re-measure
src = open(P, encoding="utf-8", errors="ignore").read().replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
anc = "printf '%s' \"$FULL_PROMPT\" > /tmp/velaris_intro_prompt.txt"
src = src.replace(anc, anc + "\nexit 0", 1)
open("/tmp/c2.sh", "w", encoding="utf-8").write(src)
subprocess.run(["bash", "/tmp/c2.sh"], capture_output=True, text=True, timeout=120)
n = os.path.getsize("/tmp/velaris_intro_prompt.txt")
print(f"prompt now: {n:,} chars (~{n//4:,} tok)")
