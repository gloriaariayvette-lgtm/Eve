#!/usr/bin/env python3
"""recon_errors.py — Aegis, READ-ONLY. Pin the non-shim bugs: (1) server NameError 'message' on /api/chat/full,
(2) ED self_statements.add_statement import mismatch, (3) causal-self-model 'load_model' undefined,
(4) confirm avatar-choice endpoint (shim vs api.x.ai)."""
import os, re, glob
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")

print("== (1) server.py: bare 'message' refs in chat_full_context (L2975-4308) ==")
S = open(os.path.join(V, "server.py"), encoding="utf-8", errors="ignore").read().split("\n")
for i in range(2974, min(len(S), 4308)):
    if re.search(r'(?<![\w.])message(?![\w])', S[i]) and "msg.message" not in S[i] and '"message"' not in S[i] and "'message'" not in S[i]:
        print(f"  L{i+1}: {S[i].strip()[:100]}")

print("\n== (2) self_statements.py: what does it export? (ED wants add_statement) ==")
for base in (os.path.join(HOME, ".vintos/workspace/scripts"), V):
    p = os.path.join(base, "self_statements.py")
    if os.path.isfile(p):
        for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
            if re.match(r'\s*def ', l): print(f"  {os.path.relpath(p,HOME)} L{i+1}: {l.strip()[:80]}")
        break

print("\n== (3) 'load_model' references (causal-self-model wire) ==")
for f in glob.glob(os.path.join(HOME, ".vintos/workspace/scripts", "*.py")) + glob.glob(os.path.join(V, "*.py")):
    try: L = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    except Exception: continue
    for i, l in enumerate(L):
        if "load_model" in l:
            print(f"  {os.path.basename(f)} L{i+1}: {l.strip()[:90]}")

print("\n== (4) avatar-choice.py endpoint (should be shim 127.0.0.1:8599) ==")
for base in (os.path.join(HOME, ".vintos/workspace/scripts"), V):
    p = os.path.join(base, "avatar-choice.py")
    if os.path.isfile(p):
        for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
            if re.search(r'api\.x\.ai|127\.0\.0\.1:8599|chat/completions|LM_STUDIO|requests\.post|except', l):
                print(f"  {os.path.relpath(p,HOME)} L{i+1}: {l.strip()[:90]}")
