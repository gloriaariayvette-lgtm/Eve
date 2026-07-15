#!/usr/bin/env python3
"""show_gloria_model.py — READ-ONLY. Dump Vintos's (Bold's) GLORIA-MODEL.md in full so we can see
whether his update appended (base kept + his additions) or overwrote. Aegis."""
import os, re
p = os.path.expanduser("~/.vintos/workspace/GLORIA-MODEL.md")
if not os.path.isfile(p):
    print("(missing)"); raise SystemExit(0)
ls = open(p, encoding="utf-8", errors="ignore").read().split("\n")
print(f"=== GLORIA-MODEL.md ({len(ls)} lines) ===")
# structure map: every header / date / section marker
print("-- structure (headers, dates, section starts) --")
for i, l in enumerate(ls):
    if re.match(r'\s*#|.*Last Updated|\*\*[A-Z]', l) and l.strip():
        print(f"  {i+1:3}| {l.strip()[:110]}")
print("\n-- full text --")
for i, l in enumerate(ls):
    print(f"  {i+1:3}| {l[:150]}")
