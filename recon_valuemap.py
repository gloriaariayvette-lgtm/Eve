#!/usr/bin/env python3
"""recon_valuemap.py — Aegis, READ-ONLY, terse. value-map should be short/daily but measured 520KB. Check its
real size + structure (accumulated day-blocks = append bug?) and how it's written (append vs overwrite)."""
import os, re, glob
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".openclaw/workspace/memory")
for name in ("value-map.md", "value-map.txt"):
    p = os.path.join(MEM, name)
    if os.path.isfile(p):
        txt = open(p, encoding="utf-8", errors="ignore").read()
        dates = re.findall(r'20\d\d-\d\d-\d\d', txt)
        print(f"{name}: {len(txt):,}B, {txt.count(chr(10))+1} lines, {len(dates)} date-stamps, {len(set(dates))} unique days")
        print(f"  HEAD: {re.sub(chr(10),' ',txt[:150])}")
        print(f"  TAIL: {re.sub(chr(10),' ',txt[-150:])}")
# who writes value-map
print("-- writers of value-map --")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
n = 0
for f in glob.glob(os.path.join(SC, "*.py")) + glob.glob(os.path.join(SC, "*.sh")):
    for i, l in enumerate(open(f, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'value-map\.(md|txt)', l) and re.search(r'open\([^)]*["\']a["\']|>>|write|dump|\.md["\']?\s*,\s*["\']a', l):
            print(f"  {os.path.basename(f)}:{i+1}: {l.strip()[:88]}"); n += 1
            if n >= 8: break
    if n >= 8: break
if n == 0: print("  (no obvious append/write found — will widen if needed)")
