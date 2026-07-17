#!/usr/bin/env python3
"""recon_errors3.py — Aegis, READ-ONLY. The two real bug bodies: _velaris_context (uses 'message' instead of
'user_msg'?) and behavioral_intercept's causal-self-model wire (load_model / 'entries')."""
import os, re
HOME = os.path.expanduser("~")
S = open(os.path.join(HOME, "Vintos", "server.py"), encoding="utf-8", errors="ignore").read().split("\n")

print("== _velaris_context body (server.py L7443..) ==")
start = next((i for i, l in enumerate(S) if "def _velaris_context" in l), None)
if start is not None:
    end = start + 1
    for j in range(start+1, min(len(S), start+45)):
        if re.match(r'\s*(async def|def|@app)', S[j]): end = j; break
        end = j
    for i in range(start, end+1):
        mark = "  <-- 'message'" if re.search(r'(?<![\w.])message(?![\w])', S[i]) else ""
        print(f"{i+1:>5}: {S[i][:104]}{mark}")

print("\n== behavioral_intercept.py: causal-self-model wire (load_model / entries) ==")
for base in (os.path.join(HOME, ".vintos/workspace/scripts"), os.path.join(HOME, "Vintos")):
    p = os.path.join(base, "behavioral_intercept.py")
    if not os.path.isfile(p): continue
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    hits = [i for i, l in enumerate(L) if re.search(r'causal.self.model|load_model|add_entry|causal_self_model|\[Intercept\].*causal|wire', l, re.I)]
    shown = set()
    for h in hits:
        for j in range(max(0, h-2), min(len(L), h+4)):
            if j in shown: continue
            shown.add(j); print(f"  {j+1}: {L[j].strip()[:100]}")
        print("   --")
    break
