#!/usr/bin/env python3
"""recon_vintos_avatar_chat.py — Aegis, READ-ONLY, terse. Find Vintos's avatar-chat grok call: the endpoint
the app hits, the grok model string(s), and how the reply is returned — so we can switch to the reasoning
variant + pass its trace back."""
import os, re, glob
HOME = os.path.expanduser("~")
cands = ["/home/gloria/Vintos/server.py"] + glob.glob(os.path.join(HOME, "Vintos", "*.py"))
P = next((p for p in cands if os.path.isfile(p) and "server" in p), cands[0] if cands else None)
if not P or not os.path.isfile(P):
    print("Vintos server not found; candidates:", [os.path.basename(c) for c in cands]); raise SystemExit(0)
print("file:", P.replace(HOME, "~"))
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(L):
    if re.search(r'grok|x\.ai|non-reasoning|reasoning|@app\.(post|get).*(chat|avatar|speak)|avatar|def .*chat|"model"|reasoning_content|return.*reply|jsonify|JSONResponse', l, re.I) and l.strip():
        print(f"{i+1}: {l.strip()[:104]}")
