#!/usr/bin/env python3
"""recon_ce_genprompt.py — Aegis, READ-ONLY. To add who's-who grounding to the creative prompt cleanly,
see how the generation call assembles its system/user messages. Dump the generation heredoc verbatim
(from RESPONSE=$(python3 << ... to the write), and where SYSTEM_PROMPT / messages / USER_PROMPT are set."""
import os, re
HOME = os.path.expanduser("~")
CE = os.path.join(HOME, ".vintos/workspace/scripts/creative-expression.sh")
lines = open(CE, encoding="utf-8", errors="ignore").read().split("\n")

# find SYSTEM_PROMPT assignment(s)
print("=== SYSTEM_PROMPT / SOUL assembly ===")
for i, l in enumerate(lines):
    if re.search(r'SYSTEM_PROMPT=|SOUL=|system.*content|role.*system', l) and l.strip():
        print(f"   {i+1:4}| {l.strip()[:120]}")

# dump the generation heredoc verbatim
start = next((i for i, l in enumerate(lines) if re.search(r'RESPONSE=\$\(python3', l)), None)
if start is not None:
    print(f"\n=== generation heredoc + write (lines {start+1}..) VERBATIM ===")
    for i in range(start, min(start + 60, len(lines))):
        print(f"{i+1:4}| {lines[i][:140]}")
        if lines[i].strip().startswith('echo "ART:'):
            break
