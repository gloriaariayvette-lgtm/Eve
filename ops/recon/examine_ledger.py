#!/usr/bin/env python3
"""examine_ledger.py — Aegis, READ-ONLY, no bash/network. Confirm caps applied; examine why the ledger's
'last 20' surfaces March — entries, date range, sort order, and the exact slicing code."""
import os, re, json
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
MEM = os.path.join(HOME, ".openclaw/workspace/memory")
src = open(P, encoding="utf-8", errors="ignore").read()
print("caps applied:",
      "humor" if "head -c 4000 \"$WORKSPACE/memory/humor-profile.json\"" in src else "humor=NO",
      "| taste" if "head -c 4000 \"$WORKSPACE/memory/taste-profile.json\"" in src else "| taste=NO",
      "| valuemap" if "f.read()[-5000:]" in src else "| valuemap=NO")

lp = os.path.join(MEM, "interaction-ledger.json")
L = json.load(open(lp, encoding="utf-8", errors="ignore"))
ts = [e.get("timestamp", "") for e in L if isinstance(e, dict)]
print(f"\nledger: {len(L)} entries")
print(f"  first-in-file: {ts[0][:16] if ts else '-'}   last-in-file: {ts[-1][:16] if ts else '-'}")
print(f"  min ts: {min(ts)[:16] if ts else '-'}   max ts: {max(ts)[:16] if ts else '-'}")
print(f"  sorted ascending: {ts == sorted(ts)}")
# how many in last 30 days
import time
cut = time.time() - 30*86400
recent = 0
for x in ts:
    try:
        if time.mktime(time.strptime(x[:19], "%Y-%m-%dT%H:%M:%S")) > cut: recent += 1
    except Exception: pass
print(f"  entries within last 30 days: {recent}/{len(ts)}")

print("\n-- ledger slicing code in introspection --")
for i, l in enumerate(src.split("\n")):
    if re.search(r'interaction-ledger|INTERACTION LEDGER|\[-?20', l) and l.strip():
        print(f"  {i+1}: {l.strip()[:100]}")
