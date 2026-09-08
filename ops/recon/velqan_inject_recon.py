#!/usr/bin/env python3
"""velqan_inject_recon.py — READ-ONLY, capped. The LLM-call + prompt-assembly point in all four
reflective scripts (Vintos + Velaris journal/introspection), so the $VELQAN block slots in cleanly.
Aegis."""
import os, re, glob
HOME = os.path.expanduser("~")

def show_call(path):
    if not os.path.isfile(path):
        print("  (missing)", path.replace(HOME,'~')); return
    ls = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"\n-- {path.replace(HOME,'~')} --")
    # the LLM call + the prompt vars near it
    calls = [i for i, l in enumerate(ls) if re.search(r'chat/completions|api\.x\.ai|curl .*http|requests\.post|-d @|USER_PROMPT|USER_MSG|PROMPT=|"content"', l)]
    seen = []
    for i in calls:
        if any(abs(i-s) < 3 for s in seen): continue
        seen.append(i)
        for k in range(max(0, i-2), min(i+3, len(ls))):
            print(f"  {k+1:4}| {ls[k][:150]}")
        print("  ...")
        if len(seen) >= 5: break

# Vintos
show_call(os.path.expanduser("~/Vintos/idle-journal.sh"))
show_call(os.path.expanduser("~/Vintos/introspection.sh"))

# Velaris — find her journal + introspection
print("\n=== Velaris journal/introspection scripts ===")
vcands = glob.glob(os.path.expanduser("~/.openclaw/workspace/scripts/*journal*")) + \
         glob.glob(os.path.expanduser("~/.openclaw/workspace/scripts/*introspect*")) + \
         glob.glob(os.path.expanduser("~/.openclaw/workspace/scripts/*idle*"))
vcands = [c for c in vcands if os.path.isfile(c) and not c.endswith((".pyc", ".bak"))]
print("  found:", [os.path.basename(c) for c in vcands])
for c in vcands[:2]:
    show_call(c)
