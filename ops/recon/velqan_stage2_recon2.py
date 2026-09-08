#!/usr/bin/env python3
"""velqan_stage2_recon2.py — READ-ONLY, capped. The exact prompt-assembly point in idle-journal.sh &
introspection.sh (where a $VELQAN block goes into the generation), and where velqan-coiner writes a new
coinage (targets to mirror for Vintos + the shared log). Aegis."""
import os, re
HOME = os.path.expanduser("~")

def dump_around(path, pats, ctx_before=1, ctx_after=1, cap=8, label=""):
    if not os.path.isfile(path): print("  (missing)", path.replace(HOME,'~')); return
    ls = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"-- {path.replace(HOME,'~')} {label} --")
    shown = []; hits = 0
    for i, l in enumerate(ls):
        if re.search(pats, l) and not any(abs(i-s) < 2 for s in shown):
            shown.append(i); hits += 1
            for k in range(max(0, i-ctx_before), min(i+ctx_after+1, len(ls))):
                print(f"  {k+1:4}| {ls[k][:140]}")
            print("  ...")
            if hits >= cap: break

VIN = os.path.expanduser("~/Vintos")
VS = os.path.expanduser("~/.openclaw/workspace/scripts")

print("=== idle-journal.sh: prompt assembly + LLM call ===")
dump_around(os.path.join(VIN, "idle-journal.sh"), r'PROMPT|prompt=|curl|api\.x\.ai|chat/completions|ask_|content"|<<|EOF|"\$\{?SOUL|GLORIA_MODEL|-d ', 0, 1, 8)

print("\n=== introspection.sh: prompt assembly + LLM call ===")
dump_around(os.path.join(VIN, "introspection.sh"), r'PROMPT|prompt=|curl|api\.x\.ai|chat/completions|ask_|content"|<<|EOF|TEMPORAL|VALUE_MAP|-d ', 0, 1, 8)

print("\n=== velqan-coiner.py: where a coinage is WRITTEN (append targets) ===")
p = os.path.join(VS, "velqan-coiner.py")
if os.path.isfile(p):
    ls = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(ls):
        if re.search(r'open\([^)]*[\'"]a|\.write\(|append|dump\(|REF|UTTER|LEXICON|coinage', l) and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:4}| {l.strip()[:130]}")
