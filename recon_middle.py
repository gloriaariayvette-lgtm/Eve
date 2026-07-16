#!/usr/bin/env python3
"""recon_middle.py — Aegis, READ-ONLY, TIGHT. Map the LLM call sites so I know which are the MIDDLE (absorb/held/
audit -> should be Gemma) vs a1/b1/final (stay Claude). Tags each endpoint. For server.py show only the
chat_full_context helpers (_g / _draft). Capped."""
import os, re
HOME = os.path.expanduser("~")
EP = [("127.0.0.1:8599", "SHIM->claude"), ("172.18.16.1:1234", "GEMMA"),
      ("api.anthropic.com", "CLAUDE-direct"), ("api.x.ai", "GROK-direct")]
def tag(line):
    for s, t in EP:
        if s in line: return t
    return None

def scan(path, label, cap=30):
    if not os.path.isfile(path): print(f"== {label}: missing =="); return
    L = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"== {label} ({len(L)} lines) ==")
    n = 0
    for i, l in enumerate(L):
        t = tag(l)
        if not t: continue
        # nearest assignment/label above (a1/b1/a2/b2/held/audit/final/synthesis/integration/absorb)
        ctx = ""
        for j in range(i, max(0, i-6), -1):
            m = re.search(r'\b(a1|b1|a2|b2|held|audit\w*|final|_synthesis\w*|integration\w*|absorb\w*|_draft|_g|call_llm|claude)\b', L[j])
            if m: ctx = f"L{j+1}:{m.group(1)}"; break
        print(f"  L{i+1:<5} [{t:<13}] {ctx:<22} {l.strip()[:60]}")
        n += 1
        if n >= cap: print("   (capped)"); break

scan(os.path.join(HOME, "Vintos", "idle-journal.sh"), "idle-journal.sh")
scan(os.path.join(HOME, "Vintos", "introspection.sh"), "introspection.sh")

# server.py: only the chat_full_context helpers _g / _draft
p = os.path.join(HOME, "Vintos", "server.py")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"== server.py: _g / _draft helpers (chat_full_context) ==")
    for i, l in enumerate(L):
        if re.match(r'\s*(async\s+def|def)\s+(_g|_draft)\b', l):
            print(f"  --- {l.strip()} (L{i+1}) ---")
            for j in range(i, min(len(L), i+16)):
                if tag(L[j]) or re.search(r'model|gemma|claude|grok|endpoint|url', L[j], re.I):
                    print(f"    L{j+1}: {L[j].strip()[:78]}")
