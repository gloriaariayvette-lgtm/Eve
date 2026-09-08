#!/usr/bin/env python3
"""recon_intro_audit.py — Aegis, READ-ONLY. Print the full audit() function in introspection.sh (raw repr +
running bracket balance) to find the missing +/comma after the prompt strings."""
import os, re
P = os.path.expanduser("~/Vintos/introspection.sh")
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
s = next((i for i, l in enumerate(lines) if l.strip() == "def audit(a, b, label):"), None)
if s is None:
    s = next((i for i, l in enumerate(lines) if re.match(r'\s*def audit\(', l)), None)
if s is None: print("audit() not found"); raise SystemExit(0)
# end: next top-level def/dedent at same indent
ind = len(lines[s]) - len(lines[s].lstrip())
e = s + 1
while e < len(lines):
    l = lines[e]
    if l.strip() and (len(l)-len(l.lstrip())) <= ind and not l.lstrip().startswith(("#",)):
        break
    e += 1
bal = 0
print(f"audit() L{s+1}-{e}:")
for n in range(s, min(e+1, len(lines))):
    for ch in lines[n]:
        if ch in "([{": bal += 1
        elif ch in ")]}": bal -= 1
    print(f"  {n+1} [bal {bal:+d}]: {lines[n]!r}")
