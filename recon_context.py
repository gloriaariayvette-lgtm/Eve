#!/usr/bin/env python3
"""recon_context.py — Aegis, READ-ONLY, terse. Show how introspection builds $CONTEXT — the value-map /
pride / blush / reflection reads — so we can cap each to its recent slice."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")
# show every line that reads a big memory file or builds CONTEXT
for i, l in enumerate(L[:365]):
    if re.search(r'value-map|pride-reflection|autonomous-blush|taste-reflection|ambition-reflection|CONTEXT=|CONTEXT="|\.read\(\)|cat .*reflection|PREV_INTRO|INTRO_SEMANTIC|=\$\(cat', l) and l.strip() and not l.strip().startswith("#"):
        print(f"{i+1}: {l.strip()[:104]}")
