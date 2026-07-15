#!/usr/bin/env python3
"""recon_6b_bodies.py — Aegis, READ-ONLY. Show the two selection bodies I still need before wiring:
get_preoccupation()/set_preoccupation() in emoclaw_utils (the DREAM seed picker) and pearl-engine's
promotion/verification logic (which candidate crystallizes). Exact line ranges, so the wiring edits land
on real anchors."""
import os, re
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
def sh(p): return p.replace(HOME, "~")

def dump_range(path, a, b):
    lines = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    for i in range(a - 1, min(b, len(lines))):
        print(f"   {i+1:4}| {lines[i][:118]}")

def dump_funcs(path, name_pat, span=26, cap=4):
    lines = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    n = 0
    for i, l in enumerate(lines):
        if re.match(r'\s*def ', l) and re.search(name_pat, l):
            print(f"   -- {l.strip()[:80]} (line {i+1}) --")
            for j in range(i, min(i + span, len(lines))):
                if lines[j].strip():
                    print(f"   {j+1:4}| {lines[j][:114]}")
            n += 1
            if n >= cap: break

eu = os.path.join(SC, "emoclaw_utils.py")
print("=== emoclaw_utils: get_preoccupation / set_preoccupation (DREAM seed picker) ===")
dump_range(eu, 327, 378)

print("\n=== mirror.sh: the preoccupation-selection block (100..145) ===")
dump_range(os.path.join(SC, "mirror.sh"), 100, 145)

print("\n=== pearl-engine.py: promotion / verification (which candidate crystallizes) ===")
pe = os.path.join(SC, "pearl-engine.py")
dump_funcs(pe, r'advance|promote|verif|crystall|select|pick|evaluate|stage|check', span=22, cap=5)
