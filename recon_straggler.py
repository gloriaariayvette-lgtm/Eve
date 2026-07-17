#!/usr/bin/env python3
"""recon_straggler.py — Aegis, READ-ONLY, TIGHT. (1) The L3773 grok call in chat_full_context verbatim + how its
httpx client/URL is formed, so I can repoint it to the shim /gemma route. (2) The record point in the underscore
causality_engine.py so I can gate it like the hyphen copy."""
import os, re
HOME = os.path.expanduser("~")

print("== server.py L3755-3800 (the L3773 grok call) ==")
p = os.path.join(HOME, "Vintos", "server.py")
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
for i in range(3754, 3800):
    print(f"{i+1:>4}: {L[i]}")
# where is `client` built (base_url) in the chatfull region?
print("\n== nearest client/AsyncClient/base_url above L3773 ==")
for i in range(3772, 2974, -1):
    if re.search(r'AsyncClient|client\s*=|base_url|LM_STUDIO|LLM_API|x\.ai', L[i]):
        print(f"{i+1:>4}: {L[i].strip()[:96]}")
        if L[i].count("AsyncClient") or "base_url" in L[i]: break

print("\n== causality_engine.py record area (underscore copy) ==")
p2 = os.path.join(HOME, "Vintos", "causality_engine.py")
if os.path.isfile(p2):
    L2 = open(p2, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(L2):
        if re.search(r'if added|db\.setdefault\("hypotheses"|untraceable|rec\["hypothesis"\]|no traceable', l):
            for j in range(max(0, i-1), min(len(L2), i+2)):
                print(f"{j+1:>4}: {L2[j].strip()[:96]}")
            print("   ..")
