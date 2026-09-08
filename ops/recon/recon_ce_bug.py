#!/usr/bin/env python3
"""recon_ce_bug.py — Aegis, READ-ONLY. Find the embedded python3 -c block in Vintos's creative-expression.sh
that throws `lines = [Gloria:` SyntaxError, so I can fix the quoting. Dump every python -c block that
mentions 'lines' or 'Gloria', verbatim with line numbers."""
import os, re
HOME = os.path.expanduser("~")
CE = os.path.join(HOME, ".vintos/workspace/scripts/creative-expression.sh")
lines = open(CE, encoding="utf-8", errors="ignore").read().split("\n")

# locate python3 -c blocks: from a line containing 'python3 -c' to the closing '")' or '"'
blocks = []
i = 0
while i < len(lines):
    if "python3 -c" in lines[i]:
        start = i
        j = i + 1
        while j < len(lines) and not re.match(r'\s*"\s*\)?', lines[j]) and lines[j].strip() not in ('"', '")', '" 2>/dev/null)', '")'):
            j += 1
            if j - start > 40:
                break
        blocks.append((start, min(j, len(lines) - 1)))
        i = j + 1
    else:
        i += 1

shown = 0
for start, end in blocks:
    body = "\n".join(lines[start:end + 1])
    if re.search(r'lines\s*=|Gloria|gloria|ledger|interaction', body):
        print(f"=== python -c block lines {start+1}..{end+1} ===")
        for k in range(start, end + 1):
            print(f"{k+1:4}| {lines[k]}")
        print()
        shown += 1
        if shown >= 3:
            break
if not shown:
    print("no matching python block found; all python3 -c starts:")
    for start, end in blocks:
        print(f"  {start+1}: {lines[start].strip()[:90]}")
