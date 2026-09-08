#!/usr/bin/env python3
"""recon_intro_syntax.py — Aegis, READ-ONLY. Pinpoint the introspection.sh embedded-python syntax error:
extract the heredoc block that contains our edits, compile it, and show the exact offending line in file
context. Also reports whether the heredoc is quoted (brace-expansion risk) and shows my insertion zones."""
import os, re
P = os.path.expanduser("~/Vintos/introspection.sh")
if not os.path.isfile(P): print("introspection.sh not found"); raise SystemExit(0)
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

di = next((i for i, l in enumerate(lines) if "def _claude_sync" in l or l.strip().startswith("def call_llm")), None)
if di is None: print("call_llm/_claude_sync not found"); raise SystemExit(0)
op = next((i for i in range(di, -1, -1) if re.search(r"<<-?\s*'?\w+'?\s*$", lines[i])), None)
if op is None: print("no heredoc opener found above the block"); raise SystemExit(0)
m = re.search(r"<<-?\s*('?)(\w+)('?)\s*$", lines[op])
marker, quoted = m.group(2), bool(m.group(1))
cl = next((i for i in range(di, len(lines)) if lines[i].strip() == marker), len(lines))
print(f"heredoc: opener L{op+1}  marker={marker}  quoted={quoted}  (unquoted => bash brace-expands {{a,b}} !)")
print(f"block: file L{op+2}..L{cl}  ({cl-op-1} lines)\n")

block = "\n".join(lines[op+1:cl])
try:
    compile(block, P, "exec")
    print("block COMPILES OK — the error must be a different heredoc/run path.")
except SyntaxError as e:
    fl = op + 1 + (e.lineno or 1)   # file line of the error
    print(f"SYNTAX ERROR at block line {e.lineno} -> FILE line {fl}: {e.msg}")
    lo = max(0, fl-8)
    for n in range(lo, min(len(lines), fl+4)):
        mark = ">>" if n == fl-1 else "  "
        print(f"{mark} {n+1}: {lines[n][:112]}")

print("\n--- my insertion zones ---")
for i, l in enumerate(lines):
    if any(s in l for s in ("_claude_sync(", "override the Gemma", "a1/b1 on claude", "final, _ = _claude_sync")):
        print(f"  {i+1}: {l.strip()[:96]}")
