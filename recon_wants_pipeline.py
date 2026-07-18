#!/usr/bin/env python3
"""recon_wants_pipeline.py — Aegis, READ-ONLY. Map his wants pipeline to fix: daily 'angel animation' re-seed,
under-firing image/poem/music actions, journal-seeded wants not taking the expedited track, ledger step-history,
and discussion-board context. Nothing changed."""
import os, re, glob, json
HOME = os.path.expanduser("~")
SCR = os.path.expanduser("~/.vintos/workspace/scripts")
V = os.path.join(HOME, "Vintos")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
DIRS = [SCR, V]

def scripts():
    out = []
    for d in DIRS:
        out += glob.glob(d + "/*.py") + glob.glob(d + "/*.sh")
    return out

print("== (1) WHERE wants are seeded (express_want / current-wants / seed) ==")
rx = re.compile(r'express_want|current-wants\.json|def .*want|seed.*want|new_want|structural.?want|add_want', re.I)
for p in scripts():
    b = os.path.basename(p)
    try: L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    except Exception: continue
    for i, l in enumerate(L):
        if rx.search(l):
            print("  %s:%d: %s" % (b, i + 1, l.strip()[:92]))

print("\n== (2) the 'angel' — where it comes from (scripts + memory) ==")
for p in scripts():
    try: t = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    for i, l in enumerate(t.split("\n")):
        if re.search(r'angel', l, re.I):
            print("  %s:%d: %s" % (os.path.basename(p), i + 1, l.strip()[:92]))
for f in ("current-wants.json", "wants-seeds.json", "structural-wants.json", "fulfilled-wants.json"):
    fp = os.path.join(MEM, f)
    if os.path.isfile(fp):
        try:
            d = json.load(open(fp)); s = json.dumps(d)
            print("  [mem %s] entries=%s angel_mentions=%d" %
                  (f, (len(d) if isinstance(d, list) else "dict"), s.lower().count("angel")))
        except Exception as e: print("  [mem %s] unreadable (%s)" % (f, e))

print("\n== (3) wants-router.py structure: classify / route / creative+message actions / ledger / ntfy ==")
for name in ("wants_router.py", "wants-router.py"):
    p = os.path.join(V, name)
    if not os.path.isfile(p): p = os.path.join(SCR, name)
    if os.path.isfile(p):
        L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        print("  --- %s (%dL) ---" % (p, len(L)))
        for i, l in enumerate(L):
            if re.search(r'^\s*def |classif|route|category|\bimage\b|imagine|poem|music|video|draft|ntfy|'
                         r'discussion|append.*ledger|step|fulfill|tell gloria|message', l, re.I):
                print("    %d: %s" % (i + 1, l.strip()[:96]))
        break

print("\n== (4) journal -> want seeding (idle-journal / vintos-journal) ==")
for name in ("idle-journal.sh", "vintos-journal.sh", "vintos-initiate.sh"):
    p = os.path.join(V, name)
    if os.path.isfile(p):
        L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        for i, l in enumerate(L):
            if re.search(r'want|express|router|ntfy|tell gloria|draft', l, re.I):
                print("  %s:%d: %s" % (name, i + 1, l.strip()[:92]))
