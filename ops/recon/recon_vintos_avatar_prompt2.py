#!/usr/bin/env python3
"""recon_vintos_avatar_prompt2.py — Aegis, READ-ONLY, no LLM. Resolve which avatar_chat route is live, and
print the PROMPT-ASSEMBLY portion of the primary avatar_chat verbatim: where context gets concatenated into
the system string, the [DO/TOUCH/COMMAND] gesture spec, the grounding/subconscious block, and the grok
payload (model / reasoning / messages). Bounded."""
import os, re, glob
HOME = os.path.expanduser("~")
P = next((p for p in (["/home/gloria/Vintos/server.py"] + glob.glob(os.path.join(HOME, "Vintos", "server.py")))
          if os.path.isfile(p)), None)
if not P:
    print("server.py not found"); raise SystemExit(0)
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
print("file:", P.replace(HOME, "~"), "\n")

# 1) both avatar_chat defs + the decorators just above (route registration => which wins)
print("===== avatar_chat routes (last-registered wins in FastAPI) =====")
for i, l in enumerate(lines):
    if re.match(r'\s*async\s+def\s+avatar_chat\b', l):
        for k in range(max(0, i - 4), i + 1):
            if lines[k].strip():
                print(f"  {k+1}: {lines[k].strip()[:96]}")
        print("  --")

# 2) primary avatar_chat (L7699): find the system-prompt assembly + grok call, print verbatim bounded
START = next((i for i, l in enumerate(lines) if re.match(r'\s*async\s+def\s+avatar_chat\b', l)), None)
if START is None:
    raise SystemExit(0)
# region end = next top-level def/route after START
ind = len(lines[START]) - len(lines[START].lstrip())
END = START + 1
while END < len(lines):
    l = lines[END]
    if l.strip() and (len(l) - len(l.lstrip())) <= ind and re.match(r'\s*(async\s+def|def|@app)', l):
        break
    END += 1

# anchor: first line that starts assembling the system prompt string
asm = next((n for n in range(START, END) if re.search(r'\b(system|system_prompt|sys_prompt|prompt)\s*=\s*(f?["\']|.*\+)', lines[n])), START + 80)
# grok call line
callline = next((n for n in range(START, END) if re.search(r'x\.ai|chat/completions', lines[n])), END)
lo = max(START, asm - 2)
hi = min(END, max(callline + 12, asm + 180))

seg, budget = [], 11000
size = 0
for n in range(lo, hi):
    row = f"{n+1}: {lines[n]}"
    if size + len(row) > budget:
        seg.append("   ...[truncated — raise budget if you need the rest]"); break
    seg.append(row); size += len(row) + 1
print(f"\n===== avatar_chat PROMPT ASSEMBLY + GROK CALL  (L{lo+1}-{hi}, of def L{START+1}-{END}) =====")
print("\n".join(seg))
