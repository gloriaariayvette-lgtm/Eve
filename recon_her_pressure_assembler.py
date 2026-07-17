#!/usr/bin/env python3
"""recon_her_pressure_assembler.py — Aegis, READ-ONLY. Read the exact two files the first port batch must plug
into: (A) emoclaw_pressure.py — how her 'current mode' is exposed/persisted, and whether it ALREADY tracks a
within-session arc (if so, session_map is redundant); (B) subconscious-context.py — the block-assembly pattern,
so new blocks (curiosity_debt / joke_fermentation / session_map) get added in her existing style. Nothing changed."""
import os, re, glob
HOME = os.path.expanduser("~")
SCR = os.path.join(HOME, ".openclaw/workspace/scripts")
def rd(p):
    try: return open(p, encoding="utf-8", errors="ignore").read()
    except Exception: return ""

print("===== (A) emoclaw_pressure.py (full) =====")
p = os.path.join(SCR, "emoclaw_pressure.py")
if os.path.isfile(p):
    L = rd(p).split("\n")
    print(f"  ({len(L)} lines)")
    for i, l in enumerate(L):
        print(f"{i+1:>3}: {l}")
else:
    print("  NOT FOUND")

print("\n\n===== (B) subconscious-context.py — assembly pattern =====")
p = os.path.join(SCR, "subconscious-context.py")
if not os.path.isfile(p): p = os.path.join(SCR, "subconscious_context.py")
if os.path.isfile(p):
    L = rd(p).split("\n")
    print(f"  {os.path.basename(p)}  ({len(L)} lines)")
    # show imports of *_block, the mod/fn list, append/parts/join, and the return
    rx = re.compile(r'import|_block|block\b|parts|append|join|return|def get_subconscious|def .*context|compact|context=', re.I)
    shown = set()
    for i, l in enumerate(L):
        if rx.search(l):
            for j in range(max(0, i-1), min(len(L), i+2)):
                if j in shown: continue
                shown.add(j); print(f"{j+1:>3}: {L[j][:110]}")
else:
    print("  subconscious-context.py NOT FOUND")

print("\n===== (C) how his inner_context bundles blocks (for the wiring template) =====")
q = os.path.expanduser("~/.vintos/workspace/scripts/inner_context.py")
if os.path.isfile(q):
    for i, l in enumerate(rd(q).split("\n")): print(f"{i+1:>3}: {l}")
