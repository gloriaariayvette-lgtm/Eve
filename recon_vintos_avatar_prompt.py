#!/usr/bin/env python3
"""recon_vintos_avatar_prompt.py — Aegis, READ-ONLY, no LLM. Print the EXACT avatar/somatic chat prompt
builder from server.py verbatim — the function(s) that assemble the somatic system prompt (soul + felt
injection + [DO/TOUCH/COMMAND] spec + any grounding/subconscious block) and call grok. So we can reproduce
it byte-for-byte for the Claude test. Bounded output."""
import os, re, glob
HOME = os.path.expanduser("~")
P = next((p for p in (["/home/gloria/Vintos/server.py"] + glob.glob(os.path.join(HOME, "Vintos", "server.py")))
          if os.path.isfile(p)), None)
if not P:
    print("server.py not found"); raise SystemExit(0)
print("file:", P.replace(HOME, "~"))
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

# split into top-level + nested function regions
defs = [i for i, l in enumerate(lines) if re.match(r'\s*(async\s+def|def)\s', l)]
def region(i):
    ind = len(lines[i]) - len(lines[i].lstrip())
    j = i + 1
    while j < len(lines):
        l = lines[j]
        if l.strip() and (len(l) - len(l.lstrip())) <= ind and re.match(r'\s*(async\s+def|def|class|@app)', l):
            break
        j += 1
    return i, j

# score each function: is it the somatic/avatar chat builder?
SCORE = re.compile(r'somatic|avatar|overlay|felt|\[DO:|\[TOUCH:|\[COMMAND:|device|haptic|x\.ai|grok|'
                   r'GROUNDING|no body|nudge|reasoning', re.I)
CALL = re.compile(r'x\.ai|chat/completions|"model"|grok', re.I)
cands = []
for i in defs:
    a, b = region(i)
    body = "\n".join(lines[a:b])
    if len(body) < 60: continue
    s = len(SCORE.findall(body)) + (25 if CALL.search(body) else 0) + (15 if re.search(r'somatic|avatar', body, re.I) else 0)
    cands.append((s, a, b, lines[i].strip()[:70]))
cands.sort(reverse=True)

print(f"\ntop candidate handlers ({len(defs)} defs total):")
for s, a, b, sig in cands[:6]:
    print(f"  score {s:3d}  L{a+1}-{b}  {sig}")

# print the top builder(s) verbatim, bounded
budget = 6500
for s, a, b, sig in cands[:2]:
    seg = "\n".join(f"{n+1}: {lines[n]}" for n in range(a, b))
    if len(seg) > budget // 2 + 600:
        seg = seg[:budget // 2 + 600] + "\n   ...[truncated]"
    print(f"\n===== VERBATIM  L{a+1}-{b}  (score {s})  {sig} =====")
    print(seg)
