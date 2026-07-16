#!/usr/bin/env python3
"""recon_causality.py — Aegis, READ-ONLY, TIGHT. Why is causality spamming his UNRESOLVED threads? Locate the
thread store, show recent entries (the spam), and the causality code that writes threads / hypotheses. Capped."""
import os, glob, json, re, time
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")

# 1. thread / causal stores
print("== thread & causal stores ==")
cands = []
for pat in ("*thread*", "*unresolved*", "*causal*", "*hypothes*"):
    cands += glob.glob(os.path.join(MEM, pat))
for f in sorted(set(cands)):
    if os.path.isfile(f):
        age = time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(f)))
        print(f"  {os.path.getsize(f):>8}  {age}  {os.path.basename(f)}")

# 2. tail of the most-recently-modified thread store (the spam)
threadish = [f for f in set(cands) if os.path.isfile(f) and ("thread" in os.path.basename(f).lower() or "unresolved" in os.path.basename(f).lower())]
threadish.sort(key=lambda f: os.path.getmtime(f), reverse=True)
for f in threadish[:1]:
    print(f"\n== recent entries in {os.path.basename(f)} ==")
    try:
        d = json.load(open(f, encoding="utf-8"))
        arr = d if isinstance(d, list) else next((d[k] for k in ("threads","unresolved","entries","items") if isinstance(d.get(k), list)), None)
        if isinstance(arr, list):
            print(f"  total entries: {len(arr)}")
            for e in arr[-8:]:
                s = e.get("thread") or e.get("text") or e.get("content") or e.get("hypothesis") or json.dumps(e, ensure_ascii=False)
                ts = e.get("timestamp") or e.get("created") or ""
                print(f"    [{str(ts)[:16]}] {str(s)[:78]}")
        else:
            print("  (not a list; keys: " + ", ".join(list(d.keys())[:12]) + ")" if isinstance(d, dict) else "  (unknown shape)")
    except Exception as e:
        print(f"  unreadable ({e})")

# 3. causality writers
print("\n== causality code that writes threads/hypotheses ==")
RX = re.compile(r'thread|unresolved|hypothes|append|json\.dump|open\([^)]*[\'"]w|add_|create_|spam|dedup', re.I)
for name in ("causality-engine.py", "causality_engine.py", "causal-cluster.py"):
    p = os.path.join(HOME, "Vintos", name)
    if not os.path.isfile(p): continue
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    hits = [(i+1, l.strip()) for i, l in enumerate(L) if l.strip() and RX.search(l)]
    print(f"  --- {name} ({len(hits)} hits) ---")
    for ln, t in hits[:16]:
        print(f"    {ln}: {t[:86]}")
    if len(hits) > 16: print(f"    ... +{len(hits)-16} more")
