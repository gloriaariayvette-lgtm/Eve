#!/usr/bin/env python3
"""recon_avatar_grokcall.py — Aegis, READ-ONLY, no LLM. Print the splice site: within the LIVE avatar_chat
(L7699), from the inference call through the reply handling and return — so the BIS/Claude-primary patch
targets the exact code. Bounded."""
import os, re, glob
HOME = os.path.expanduser("~")
P = next((p for p in (["/home/gloria/Vintos/server.py"] + glob.glob(os.path.join(HOME, "Vintos", "server.py")))
          if os.path.isfile(p)), None)
if not P: print("server.py not found"); raise SystemExit(0)
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

START = next((i for i, l in enumerate(lines) if re.match(r'\s*async\s+def\s+avatar_chat\b', l)), None)
if START is None: print("avatar_chat not found"); raise SystemExit(0)
ind = len(lines[START]) - len(lines[START].lstrip())
END = START + 1
while END < len(lines):
    l = lines[END]
    if l.strip() and (len(l) - len(l.lstrip())) <= ind and re.match(r'\s*(async\s+def|def|@app)', l):
        break
    END += 1

# first inference call inside the function
call = next((n for n in range(START, END)
             if re.search(r'chat/completions|x\.ai|LM_STUDIO|LLM_API|\.post\(|acompletion|client\.post', lines[n])), START)
lo = max(START, call - 6)
print(f"live avatar_chat L{START+1}-{END} | inference call ~L{call+1} | printing L{lo+1}-{END}\n")
seg, size, budget = [], 0, 10000
for n in range(lo, END):
    row = f"{n+1}: {lines[n]}"
    if size + len(row) > budget:
        seg.append("   ...[truncated]"); break
    seg.append(row); size += len(row) + 1
print("\n".join(seg))
