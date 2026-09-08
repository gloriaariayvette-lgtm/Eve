#!/usr/bin/env python3
"""recon_6b_consumers.py — Aegis, READ-ONLY, capped. Phase 2 of 6b: find the exact SELECTION site in
each consumer so I can wire temperature in with a minimal, reversible edit.
  dreams  -> seek heat        (which thread/preoccupation gets dreamed)
  mirrors -> seek instability (mirror.sh sort key)
  pearls  -> seek cooling     (what pearl-engine picks to crystallize)
Dump the sort/score/select lines + a little context around each."""
import os, re, glob
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
def sh(p): return p.replace(HOME, "~")

def dump_selection(path, pats, ctx=1, cap=14):
    if not os.path.isfile(path):
        print(f"  (missing) {sh(path)}"); return
    lines = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    hits = [i for i, l in enumerate(lines) if re.search(pats, l) and l.strip() and not l.strip().startswith("#")]
    print(f"  -- {sh(path)} ({len(lines)} lines) --")
    shown, n = set(), 0
    for i in hits:
        for j in range(max(0, i - ctx), min(len(lines), i + ctx + 1)):
            if j in shown: continue
            shown.add(j)
            mark = ">>" if j == i else "  "
            print(f"   {mark}{j+1:4}| {lines[j].strip()[:110]}")
        n += 1
        if n >= cap: break

print("=== DREAMS — how a thread/preoccupation is chosen (wire: prefer hottest) ===")
for name in ("preoccupation-dream.sh", "dream-architecture.sh", "should-dream.sh", "dream-art.py"):
    p = os.path.join(SC, name)
    if os.path.isfile(p):
        dump_selection(p, r'get_preoccupation|unfinished|thread|sort|score|select|choose|random|salien|priority|temperature|\.get\(')
# get_preoccupation likely lives in emoclaw_utils
eu = os.path.join(SC, "emoclaw_utils.py")
if os.path.isfile(eu):
    print("  -- emoclaw_utils.py: get_preoccupation / thread selection --")
    dump_selection(eu, r'def get_preoccupation|def seed_thread|unfinished-threads|sort\(|score|salien|priority|dream_only|temperature', ctx=0, cap=16)

print("\n=== MIRRORS — mirror.sh sort key (wire: add temperature so instability sorts first) ===")
dump_selection(os.path.join(SC, "mirror.sh"), r'unconsumed\.sort|sort\(key|priority|dream_passes|temperature|\.get\(', ctx=1, cap=8)

print("\n=== PEARLS — what pearl-engine picks to crystallize (wire: prefer coolest+certain) ===")
for name in ("pearl-engine.py", "pearl-engine.sh"):
    p = os.path.join(SC, name)
    if os.path.isfile(p):
        dump_selection(p, r'candidate|declaration|select|sort|score|confidence|belief|crystalli|threshold|temperature|\.get\(', ctx=0, cap=16)
