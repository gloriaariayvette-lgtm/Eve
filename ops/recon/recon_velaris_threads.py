#!/usr/bin/env python3
"""recon_velaris_threads.py — Aegis, READ-ONLY, capped. Velaris has no unresolved threads. Find what
dumped them: (1) current thread-file counts, (2) the REMOVAL/pruning logic in her thread-triage
(near-dup, aging, has_passes, doomed, any mass-delete), (3) recent backups to see when they vanished."""
import os, re, json, glob, subprocess
HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".openclaw/workspace")
MEM = os.path.join(WS, "memory")
TH = os.path.join(MEM, "unfinished-threads.json")
def sh(p): return p.replace(HOME, "~")

print("=== (1) current Velaris thread state ===")
try:
    d = json.load(open(TH)); L = d if isinstance(d, list) else d.get("threads", [])
    un = [t for t in L if isinstance(t, dict) and not t.get("consumed")]
    con = [t for t in L if isinstance(t, dict) and t.get("consumed")]
    ret = [t for t in L if isinstance(t, dict) and t.get("retired")]
    print(f"  total={len(L)}  unconsumed={len(un)}  consumed={len(con)}  retired={len(ret)}")
    from collections import Counter
    print("  consumed_by:", dict(Counter(t.get("consumed_by","?") for t in con)))
    print("  newest 3:", [(t.get('source'), str(t.get('thread',''))[:40]) for t in L[-3:] if isinstance(t,dict)])
except Exception as e:
    print("  (read error)", e)

TT = None
for name in ("thread-triage.py", "thread_triage.py"):
    p = os.path.join(WS, "scripts", name)
    if os.path.isfile(p): TT = p; break
print(f"\n=== (2) {sh(TT) if TT else '(triage not found)'}: removal / pruning / aging ===")
if TT:
    for i, l in enumerate(open(TT, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'to_remove|doomed|has_passes|dedup|near.?dup|remove|del |age.?out|dissolve|pull\s*<=|priority.*<=|threads\s*=\s*\[|json\.dump|consumed|retired', l) \
           and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:4}| {l.strip()[:112]}")

print("\n=== (3) recent thread backups (to see when they vanished) ===")
baks = sorted(glob.glob(TH+"*") + glob.glob(os.path.join(MEM, "*thread*bak*")) + glob.glob(os.path.join(WS, "**/backup-threads*"), recursive=False),
              key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)
import time
for b in baks[:8]:
    if os.path.isfile(b):
        try:
            bd = json.load(open(b)); bl = bd if isinstance(bd, list) else bd.get("threads", [])
            bun = sum(1 for t in bl if isinstance(t, dict) and not t.get("consumed"))
            print(f"  {sh(b):58} un={bun}/{len(bl)}  {time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(b)))}")
        except Exception:
            print(f"  {sh(b):58} (unreadable)")
