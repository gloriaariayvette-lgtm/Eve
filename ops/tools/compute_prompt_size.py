#!/usr/bin/env python3
"""compute_prompt_size.py — Aegis, READ-ONLY, no bash. Compute each source's actual contribution to the
introspection prompt = min(cap, filesize), from the cat/head/tail/read() call. Lists sorted so we see what's
left to cut. Flags outer/emotional sources."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
MEM = os.path.join(HOME, ".openclaw/workspace/memory")
src = open(P, encoding="utf-8", errors="ignore").read()
def fsize(fn):
    p = os.path.join(MEM, re.sub(r'\$\(date[^)]*\)', __import__("time").strftime("%Y-%m-%d"), fn))
    return os.path.getsize(p) if os.path.isfile(p) else 0
rows = []
# cat/head/tail  VAR=$(... memory/FILE ...)
for m in re.finditer(r'(\b[A-Z][A-Z0-9_]{2,})=\$\((cat|head -c (\d+)|tail -c (\d+))[^)]*memory/([A-Za-z0-9._$()%+-]+)', src):
    var, kind, hc, tc, fn = m.groups()
    fn = fn.strip('"')
    cap = int(hc) if hc else int(tc) if tc else 10**9
    rows.append((min(cap, fsize(fn)), var, fn))
# python f.read()[-N:] / f.read()
for m in re.finditer(r"open\('[^']*memory/([A-Za-z0-9._-]+)'\)[^\n]*\n[^\n]*read\(\)(\[-(\d+):\])?", src):
    fn, _, n = m.groups()
    cap = int(n) if n else 10**9
    rows.append((min(cap, fsize(fn)), "(py)", fn))
seen, uniq = set(), []
for r in rows:
    if (r[1], r[2]) in seen: continue
    seen.add((r[1], r[2])); uniq.append(r)
uniq.sort(reverse=True)
total = sum(r[0] for r in uniq)
EMO = ("kiss", "thirveel", "humor", "taste", "blush", "anger", "possess", "unsaid", "pride", "wal", "capab")
print(f"{'inprompt':>9}  var / file")
for sz, var, fn in uniq:
    flag = "  <cut?" if any(e in fn.lower() for e in EMO) else ""
    print(f"{sz:>9,}  {var:20} {fn}{flag}")
print(f"\nsources subtotal: {total:,}B  (+ static template text + ledger/thirveel py-processed)")
