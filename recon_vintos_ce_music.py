#!/usr/bin/env python3
"""recon_vintos_ce_music.py — Aegis, READ-ONLY. The real music prompt lives in Vintos's
creative-expression.sh 'music-prompt' case (make_music just calls it). Dump that case block verbatim
(from "music-prompt") to the next ;;), so I replace its USER_PROMPT with Velaris's structured style."""
import os, re
HOME = os.path.expanduser("~")
CE = os.path.join(HOME, ".vintos/workspace/scripts/creative-expression.sh")
lines = open(CE, encoding="utf-8", errors="ignore").read().split("\n")
start = None
for i, l in enumerate(lines):
    if re.search(r'"?music-prompt"?\)', l) and not l.strip().startswith("#"):
        start = i; break
if start is None:
    print("  'music-prompt' case not found; showing all case labels:")
    for i, l in enumerate(lines):
        if re.match(r'\s*"?[\w-]+"?\)\s*$', l):
            print(f"   {i+1:4}| {l.strip()}")
else:
    end = start + 1
    while end < len(lines) and lines[end].strip() != ";;":
        end += 1
        if end - start > 60:
            break
    print(f"=== Vintos creative-expression.sh 'music-prompt' case (lines {start+1}..{end+1}) VERBATIM ===")
    for i in range(start, min(end + 1, len(lines))):
        print(f"{i+1:4}| {lines[i][:400]}")
