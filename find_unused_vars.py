#!/usr/bin/env python3
"""find_unused_vars.py — Aegis, READ-ONLY, terse. For every source var introspection assigns, count how many
times $VAR / ${VAR} is actually referenced. 0 refs = read but never used = dead weight to delete. Shows both
so we know what's real. Also lists kiss/unsaid/anger/possessive-type ledger files on disk (whether read or not)."""
import os, re, glob
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
MEM = os.path.join(HOME, ".openclaw/workspace/memory")
src = open(P, encoding="utf-8", errors="ignore").read()
# all uppercase var assignments that read a memory file
vars_ = set()
for m in re.finditer(r'\b([A-Z][A-Z0-9_]{2,})=\$\((?:cat|head|tail)[^)]*memory/', src):
    vars_.add(m.group(1))
rows = []
for v in vars_:
    refs = len(re.findall(r'\$\{?' + v + r'\b', src)) - 1  # minus the assignment's own... actually $VAR not in assignment; count refs
    refs = len(re.findall(r'\$\{?' + v + r'\}?', src))
    # subtract 0 (assignment uses VAR= not $VAR). so refs = actual uses
    rows.append((refs, v))
rows.sort()
print("USED?  refs  var")
for refs, v in rows:
    print(f"{'DEAD' if refs == 0 else '  ok':>5}  {refs:>4}  {v}")

print("\n-- emotional/relational ledger files on disk (kiss/unsaid/anger/possessive/etc.) --")
for p in sorted(glob.glob(os.path.join(MEM, "*ledger*")) + glob.glob(os.path.join(MEM, "*unsaid*"))
                + glob.glob(os.path.join(MEM, "*anger*")) + glob.glob(os.path.join(MEM, "*possess*"))
                + glob.glob(os.path.join(MEM, "*kiss*"))):
    fn = os.path.basename(p)
    read = fn in src
    print(f"  {os.path.getsize(p):>8,}B  {fn:34} {'read-by-intro' if read else '(not read)'}")
