#!/usr/bin/env python3
"""recon_vintos_makemusic.py — Aegis, READ-ONLY. make_music is ALREADY wired on Vintos; only its PROMPT
STYLE needs to match Velaris's. Dump Vintos wants-router.py make_music() verbatim (its grok prompt), and
Velaris's want-variant music prompt verbatim, so the replacement is exact."""
import os, re
HOME = os.path.expanduser("~")
WR = os.path.join(HOME, ".vintos/workspace/scripts/wants-router.py")
CE = os.path.join(HOME, ".openclaw/workspace/scripts/creative-expression.sh")
def sh(p): return p.replace(HOME, "~")

print("=== VINTOS wants-router.py — make_music() function VERBATIM ===")
lines = open(WR, encoding="utf-8", errors="ignore").read().split("\n")
# find def make_music and print until the next top-level def
start = next((i for i, l in enumerate(lines) if re.match(r'\s*def make_music\b', l)), None)
if start is not None:
    end = start + 1
    while end < len(lines) and not (re.match(r'def \w', lines[end]) or re.match(r'\S', lines[end]) and lines[end].startswith("def ")):
        if re.match(r'def \w', lines[end]) and end > start + 1:
            break
        end += 1
        if end - start > 70:
            break
    for i in range(start, min(end, len(lines))):
        print(f"{i+1:4}| {lines[i]}")
else:
    print("  (make_music not found)")

print("\n=== VELARIS creative-expression.sh — the WANT-variant music prompt (line ~221) VERBATIM ===")
clines = open(CE, encoding="utf-8", errors="ignore").read().split("\n")
for i in range(214, min(226, len(clines))):
    print(f"{i+1:4}| {clines[i][:400]}")
