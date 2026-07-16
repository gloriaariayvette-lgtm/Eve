#!/usr/bin/env python3
"""recon_chatfull.py — Aegis, READ-ONLY, TIGHT. Map chat_full_context's LLM pipeline so I know if any MIDDLE
call still uses grok (server.py was excluded from the fleet swap). Find the handler, scan its body for stage +
endpoint markers. Capped."""
import os, re
p = os.path.expanduser("~/Vintos/server.py")
if not os.path.isfile(p): print("server.py not found"); raise SystemExit(0)
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
starts = [i for i, l in enumerate(L) if re.search(r'def chat_full_context', l)]
print(f"chat_full_context defs at: {[s+1 for s in starts]}")
if not starts: raise SystemExit(0)
s = starts[0]
RX = re.compile(r'claude_draft|gemma_call|_g\(|_draft\(|api\.x\.ai|127\.0\.0\.1:8599|172\.18\.16\.1|'
                r'grok|\baudit|\bheld\b|absorb|integration|_synthesis|\bfinal\b|_g\b|route_reply', re.I)
n = 0
for i in range(s, min(len(L), s + 470)):
    if RX.search(L[i]):
        ep = ""
        for k, t in (("127.0.0.1:8599", "[SHIM]"), ("172.18.16.1", "[GEMMA]"), ("api.x.ai", "[GROK]"),
                     ("claude_draft", "[claude]"), ("gemma_call", "[gemma]")):
            if k in L[i]: ep = t; break
        print(f"  L{i+1:<5} {ep:<8} {L[i].strip()[:82]}")
        n += 1
        if n >= 40: print("   (capped)"); break
