#!/usr/bin/env python3
"""recon_intro_syntax2.py — Aegis, READ-ONLY. Show the EXACT introspection.sh break: compile the embedded
block, print the SyntaxError's line/offset/text, and repr() the surrounding lines (reveals smart quotes,
stray chars, real newlines, missing +/comma)."""
import os, re
P = os.path.expanduser("~/Vintos/introspection.sh")
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
di = next((k for k, l in enumerate(lines) if l.strip().startswith("def call_llm") or "def _claude_sync" in l), None)
op = next((k for k in range(di, -1, -1) if re.search(r"<<-?\s*'?\w+'?\s*$", lines[k])), None)
marker = re.search(r"<<-?\s*'?(\w+)'?\s*$", lines[op]).group(1)
cl = next((k for k in range(di, len(lines)) if lines[k].strip() == marker), len(lines))
block = "\n".join(lines[op+1:cl])
try:
    compile(block, P, "exec")
    print("block compiles clean — the failing run may be a different heredoc; tell me.")
except SyntaxError as e:
    fl = op + 1 + (e.lineno or 1)
    print(f"SyntaxError: {e.msg}")
    print(f"  block line {e.lineno}, col {e.offset}  ->  FILE line {fl}")
    print(f"  e.text = {e.text!r}")
    print("\n--- repr of surrounding file lines ---")
    for n in range(max(0, fl-9), min(len(lines), fl+5)):
        tag = ">>" if n == fl-1 else "  "
        print(f"{tag} {n+1}: {lines[n]!r}")
