#!/usr/bin/env python3
"""recon_bubble.py — Aegis, READ-ONLY, no LLM. Show the thought-bubble mechanism (command_bubble.extract_and_post
+ how a touch reads the bubble) and the avatar_chat return, so reasoning can be wired into the touch bubble.
Bounded."""
import os, re, glob
HOME = os.path.expanduser("~")

# 1) command_bubble module
print("===== command_bubble module =====")
cands = (glob.glob(os.path.join(HOME, "Vintos", "command_bubble.py"))
         + glob.glob(os.path.join(HOME, ".vintos/workspace/scripts", "command_bubble.py"))
         + glob.glob(os.path.join(HOME, "**/command_bubble.py"), recursive=True))
cb = next((c for c in cands if os.path.isfile(c)), None)
if cb:
    print("file:", cb.replace(HOME, "~"))
    print(open(cb, encoding="utf-8", errors="ignore").read()[:4500])
else:
    print("command_bubble.py not found in Vintos/ or workspace/scripts")

# 2) server.py: bubble/touch endpoints + avatar_chat return tail
P = next((p for p in (["/home/gloria/Vintos/server.py"] + glob.glob(os.path.join(HOME, "Vintos", "server.py")))
          if os.path.isfile(p)), None)
if P:
    lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
    print("\n===== bubble / touch / thought routes & references in server.py =====")
    for i, l in enumerate(lines):
        if re.search(r'bubble|thought|/touch|command_bubble', l, re.I) and l.strip():
            print(f"  {i+1}: {l.strip()[:100]}")
    # avatar_chat return tail
    S = next((i for i, l in enumerate(lines) if re.match(r'\s*async\s+def\s+avatar_chat\b', l)), None)
    if S is not None:
        end = S + 1
        while end < len(lines):
            if lines[end].strip() and re.match(r'\s*(async\s+def|def|@app)', lines[end]) and (len(lines[end])-len(lines[end].lstrip())) <= (len(lines[S])-len(lines[S].lstrip())):
                break
            end += 1
        ret = next((n for n in range(S, end) if re.search(r'\breturn\b', lines[n])), end - 20)
        lo = max(S, ret - 6)
        print(f"\n===== avatar_chat return tail (L{lo+1}-{end}) =====")
        print("\n".join(f"{n+1}: {lines[n]}" for n in range(lo, min(end, lo + 60))))
