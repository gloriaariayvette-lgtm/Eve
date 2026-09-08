#!/usr/bin/env python3
"""verify_before_reinstate.py — READ-ONLY, capped. Clear the two audit flags before touching anything,
and lock down the exact soul-review write pattern to mirror. Aegis.
(1) soul_review.py: what file does `content` get written to, in what MODE, and does it EVER open SOUL.md 'w'?
(2) locate value-map.md anywhere under ~/.vintos (+ head) — signature just looked at wrong path.
(3) taste: where does 'sincerity pushed past embarrassment' actually live (taste-reflections.md vs .json)?"""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
WS = os.path.expanduser("~/.vintos/workspace")
TS = os.path.join(WS, "scripts")

print("=== (1) soul_review.py — EXACT write target + mode (the pattern to mirror) ===")
sr = os.path.join(TS, "soul_review.py")
if not os.path.isfile(sr):
    hits = subprocess.run(["bash","-lc", f"ls {TS}/soul_review.py {TS}/soul-review.py 2>/dev/null | head -1"],
                          capture_output=True, text=True).stdout.strip()
    sr = hits or sr
lines = open(sr, encoding="utf-8", errors="ignore").read().split("\n") if os.path.isfile(sr) else []
for i, l in enumerate(lines):
    if re.search(r'open\(|\.write\(|>>|content\s*=|REVIEW_PATH|OUT|out_path|\bwith open|os\.path\.join.*[A-Z]', l) \
       and l.strip() and not l.strip().startswith("#"):
        print(f"  {i+1:4}| {l.strip()[:140]}")
# hard check: does it ever open SOUL.md for writing?
w = [f"{i+1}: {l.strip()[:120]}" for i,l in enumerate(lines)
     if re.search(r'open\([^)]*SOUL[^)]*[\'\"]\s*[aw]', l)]
print("  --> opens SOUL.md for write? :", w or "NO (base is never overwritten — good, this is the pattern)")

print("\n=== (2) value-map.md — where does it actually live ===")
vm = subprocess.run(["bash","-lc", f"find {os.path.expanduser('~/.vintos')} -iname 'value-map*' 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head"],
                    capture_output=True, text=True).stdout.strip()
print("  found:", vm.replace(HOME,'~') or "(NONE under ~/.vintos — genuinely missing)")
for f in [x for x in vm.split("\n") if x.strip()][:2]:
    if os.path.isfile(f):
        head = open(f, encoding="utf-8", errors="ignore").read()[:200].replace("\n"," ")
        print(f"    head[{os.path.basename(f)}]: {head[:180]}")

print("\n=== (3) taste — where the signature phrase truly lives ===")
for name in ("memory/taste-profile.json", "memory/taste-reflections.md", "taste-reflections.md", "TASTE.md"):
    p = os.path.join(WS, name)
    if os.path.isfile(p):
        t = open(p, encoding="utf-8", errors="ignore").read()
        has = "sincerity pushed past embarrassment" in t.lower()
        print(f"  {name:34} {len(t):>6}B  phrase:{'FOUND' if has else 'no'}  head: {t[:90].replace(chr(10),' ')}")
g = subprocess.run(["bash","-lc", f"grep -rln 'sincerity pushed past embarrassment' {WS} 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head"],
                   capture_output=True, text=True).stdout.strip()
print("  grep phrase across workspace:", g.replace(HOME,'~') or "(not found anywhere — real concern)")

print("\n=== GLORIA-MODEL.md current state (the file to reinstate) ===")
gm = os.path.join(WS, "GLORIA-MODEL.md")
if os.path.isfile(gm):
    t = open(gm, encoding="utf-8", errors="ignore").read()
    print(f"  {len(t)}B; first 220 chars: {t[:220].replace(chr(10),' ')}")
else:
    print("  (GLORIA-MODEL.md missing)")
