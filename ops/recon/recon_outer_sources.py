#!/usr/bin/env python3
"""recon_outer_sources.py — Aegis, READ-ONLY, terse. List every memory file introspection reads into a var
(ledgers/emotional sources: kiss, unsaid, anger, possessive, blush, etc.) with size + whether the var is even
used in FULL_PROMPT. So we cut the unused/dead ones."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
MEM = os.path.join(HOME, ".openclaw/workspace/memory")
src = open(P, encoding="utf-8", errors="ignore").read()
# find VAR=$(... memory/<file> ...) and python open('.../memory/<file>')
rows = []
for m in re.finditer(r'(\b[A-Z_]+)=\$\((?:cat|head|tail)[^)]*?memory/([A-Za-z0-9._-]+)', src):
    rows.append((m.group(1), m.group(2)))
for m in re.finditer(r"open\('[^']*memory/([A-Za-z0-9._-]+)'\)", src):
    rows.append(("(py)", m.group(1)))
seen = set(); out = []
for var, fn in rows:
    key = (var, fn)
    if key in seen: continue
    seen.add(key)
    fp = os.path.join(MEM, fn)
    sz = os.path.getsize(fp) if os.path.isfile(fp) else 0
    # is var referenced in the FULL_PROMPT block (after line with FULL_PROMPT=)?
    used = ("$" + var) in src[src.find("FULL_PROMPT="):] if var != "(py)" else "-"
    out.append((sz, var, fn, used))
out.sort(reverse=True)
print(f"{'size':>9}  {'var':22} {'file':34} inFULL_PROMPT")
for sz, var, fn, used in out:
    print(f"{sz:>9,}  {var:22} {fn:34} {used}")
