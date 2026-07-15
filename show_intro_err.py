#!/usr/bin/env python3
"""show_intro_err.py — Aegis, READ-ONLY. Print heredoc lines 80-96 (around the SyntaxError) verbatim so we
can see and fix it."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
txt = open(P, encoding="utf-8", errors="ignore").read()
m = re.search(r"<<'PYEOF'\n(.*?)\nPYEOF", txt, re.S)
py = m.group(1).split("\n")
for i in range(78, min(len(py), 96)):
    print(f"{i+1}: {py[i]}")
