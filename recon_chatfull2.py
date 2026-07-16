#!/usr/bin/env python3
"""recon_chatfull2.py — Aegis, READ-ONLY. Full LLM map of the LIVE chat_full_context (L2975) until the function
ends. Tag every LLM call by endpoint so I can flip stray grok MIDDLE calls to Gemma while leaving a1/b1/final
(claude_draft) alone. Capped."""
import os, re
p = os.path.expanduser("~/Vintos/server.py")
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
s = 2975 - 1  # def chat_full_context
# find function end: next top-level def/async def at column 0 after s
end = len(L)
for i in range(s + 2, len(L)):
    if re.match(r'(async def |def |@app\.)', L[i]):
        end = i; break
print(f"chat_full_context body: L{s+1}..L{end}  ({end-s} lines)")
RX = re.compile(r'claude_draft|gemma_call|_g\(|_draft\(|api\.x\.ai|127\.0\.0\.1:8599|172\.18\.16\.1|'
                r'"model"|route_reply|\baudit|\bheld\b|absorb|integration|_synthesis|requests\.post|_req\.post|\.post\(', re.I)
n = 0
for i in range(s, end):
    if RX.search(L[i]):
        ep = ""
        for k, t in (("127.0.0.1:8599", "[SHIM]"), ("172.18.16.1", "[GEMMA]"), ("api.x.ai", "[GROK]"),
                     ("claude_draft", "[claude]"), ("gemma_call", "[gemma]"), ("route_reply", "[router]")):
            if k in L[i]: ep = t; break
        print(f"  L{i+1:<5} {ep:<8} {L[i].strip()[:84]}")
        n += 1
        if n >= 70: print("   (capped)"); break
