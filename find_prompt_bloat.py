#!/usr/bin/env python3
"""find_prompt_bloat.py — Aegis, READ-ONLY, terse. The 727KB bulk isn't active wants. Measure every file
introspection.sh reads (cat/open/read) sorted by size, and show the FULL_PROMPT assembly, to pin the blob."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
txt = open(P, encoding="utf-8", errors="ignore").read()
# collect referenced paths
paths = set()
for m in re.finditer(r'(?:cat|open\()\s*["\']?([~$][^\s"\')]+|/[^\s"\')]+|"\$[A-Z_]+/[^"\']+")', txt):
    paths.add(m.group(1))
# also expand $WORKSPACE/$HOME/memory refs
for m in re.finditer(r'\$\{?(?:WORKSPACE|HOME|MEMORY)\}?/([^\s"\')]+)', txt):
    paths.add("mem:" + m.group(1))
def resolve(p):
    p = p.strip('"').replace("$WORKSPACE", os.path.join(HOME, ".openclaw/workspace")).replace("$HOME", HOME)
    p = p.replace("$MEMORY", os.path.join(HOME, ".openclaw/workspace/memory")).replace("~", HOME)
    if p.startswith("mem:"): p = os.path.join(HOME, ".openclaw/workspace", p[4:])
    p = re.sub(r'\$\(date[^)]*\)', __import__("time").strftime("%Y-%m-%d"), p)
    return p
sizes = []
for p in paths:
    rp = resolve(p)
    if os.path.isfile(rp): sizes.append((os.path.getsize(rp), rp))
print("-- files introspection reads, by size --")
for sz, rp in sorted(sizes, reverse=True)[:12]:
    print(f"  {sz:>9,}B  {rp.replace(HOME,'~')}")
print("-- FULL_PROMPT assembly (what it concatenates) --")
for i, l in enumerate(txt.split("\n")):
    if re.search(r'FULL_PROMPT=|FULL_PROMPT="\$', l) and l.strip():
        for j in range(i, min(i+30, len(txt.split(chr(10))))):
            ln = txt.split(chr(10))[j]
            if ln.strip(): print(f"  {j+1}: {ln.strip()[:96]}")
        break
