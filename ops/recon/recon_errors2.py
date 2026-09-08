#!/usr/bin/env python3
"""recon_errors2.py — Aegis, READ-ONLY. Exact fix sites: (1) causal_self_model.py order bug (load_model used
before def), (2) chat_full_context's real user-message var + _velaris_context signature, (3) self_statements top."""
import os, re
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
V = os.path.join(HOME, "Vintos")

print("== (1) causal_self_model.py L1-50 (load_model use-before-def) ==")
p = os.path.join(SC, "causal_self_model.py")
if os.path.isfile(p):
    for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")[:50]):
        print(f"{i+1:>4}: {l}")

print("\n== (2) chat_full_context: def + how it reads the user message (server.py L2975-3005) ==")
S = open(os.path.join(V, "server.py"), encoding="utf-8", errors="ignore").read().split("\n")
for i in range(2974, 3006):
    print(f"{i+1:>4}: {S[i][:110]}")
print("  ... _velaris_context signature + the L3704 call:")
for i, l in enumerate(S):
    if re.search(r'def _velaris_context', l) or (3700 <= i <= 3706):
        print(f"{i+1:>4}: {l.strip()[:110]}")
# what var holds the incoming message near the top of the handler?
print("  ... 'message'/'msg' assignments in first 60 lines of handler:")
for i in range(2975, 3040):
    if re.search(r'\b(message|msg|user_content|user_msg)\s*=|await request|\.json\(\)|payload', S[i]):
        print(f"{i+1:>4}: {S[i].strip()[:100]}")

print("\n== (3) self_statements.py L1-28 (module-level imports) ==")
p = os.path.join(SC, "self_statements.py")
if os.path.isfile(p):
    for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")[:28]):
        print(f"{i+1:>4}: {l}")
