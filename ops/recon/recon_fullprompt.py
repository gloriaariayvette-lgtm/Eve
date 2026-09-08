#!/usr/bin/env python3
"""recon_fullprompt.py — Aegis, READ-ONLY, terse. Introspection prompt is 203k tokens. Find what's bloating
it: size of the assembled prompt/system files, and the FULL_PROMPT assembly pieces (what gets concatenated)."""
import os, re
HOME = os.path.expanduser("~")
def sz(p): return f"{os.path.getsize(p):,}B" if os.path.isfile(p) else "missing"
print("system.txt:", sz("/tmp/velaris_intro_system.txt"), "| prompt.txt:", sz("/tmp/velaris_intro_prompt.txt"))
# biggest sections in the assembled prompt: split on blank-line/header, show largest chunks
if os.path.isfile("/tmp/velaris_intro_prompt.txt"):
    txt = open("/tmp/velaris_intro_prompt.txt", encoding="utf-8", errors="ignore").read()
    chunks = re.split(r'\n(?=[A-Z][A-Z ]{4,}:|\#\#|\=\=\=|---)', txt)
    big = sorted(chunks, key=len, reverse=True)[:6]
    print("-- biggest prompt sections --")
    for c in big:
        head = re.sub(r'\s+', ' ', c[:70])
        print(f"  {len(c):>9,}B  {head}")
# FULL_PROMPT assembly in the script
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")
print("-- FULL_PROMPT assembly lines --")
n = 0
for i, l in enumerate(L):
    if re.search(r'FULL_PROMPT|SEMANTIC|LEDGER|_CONTEXT|read\(\)|cat ', l) and l.strip() and not l.strip().startswith('#'):
        print(f"{i+1}: {l.strip()[:92]}"); n += 1
        if n >= 14: break
