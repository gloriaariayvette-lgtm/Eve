#!/usr/bin/env python3
"""recon_generation_pipeline.py — Aegis, READ-ONLY, FAST. To test first-thought suppression ON THE ORIGINAL CALL,
find where his real response is generated with full context: the chat handler, where the system prompt / context is
ASSEMBLED (the variable that holds SOUL+self-model+relationship+everything), the bilateral LLM call(s), and where
the final response is returned — so a SHADOW reconsideration can reuse that exact assembled context, log-only.
His pipeline = merged_full_route.py + server.py. Nothing written."""
import os, re
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")

def scan(path, tag):
    if not os.path.isfile(path):
        print("  %s: (not found)" % tag); return
    L = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print("\n===== %s (%s, %d lines) =====" % (tag, path, len(L)))
    print("  -- defs --")
    for i, l in enumerate(L):
        if re.match(r'\s*def\s', l) or re.match(r'\s*async def\s', l):
            print("    %4d: %s" % (i + 1, l.strip()[:96]))
    print("  -- context/prompt assembly (the variable to reuse) --")
    for i, l in enumerate(L):
        if re.search(r'system_prompt|SYSTEM_PROMPT|system_msg|full_context|context\s*=|prompt\s*=|messages\s*=\s*\[|assemble|build_context|SOUL|self_model|relationship', l):
            print("    %4d: %s" % (i + 1, l.strip()[:100]))
        if i > 700: break
    print("  -- LLM call sites (bilateral / synthesis) --")
    for i, l in enumerate(L):
        if re.search(r'requests\.post|urlopen|/v1/chat|:8599|bilateral|A1|B1|synthes|absorb|generate|\.completion|call_llm|ask_llm', l):
            print("    %4d: %s" % (i + 1, l.strip()[:100]))
        if i > 700: break
    print("  -- where the final response is returned / sent --")
    for i, l in enumerate(L):
        if re.search(r'return .*response|return .*reply|return .*text|final_response|jsonify|\"response\"|send|emit', l, re.I):
            print("    %4d: %s" % (i + 1, l.strip()[:96]))
        if i > 700: break

for name in ("merged_full_route.py", "merged-full-route.py"):
    p = os.path.join(HIS, name)
    if os.path.isfile(p): scan(p, name); break

# server.py chat handler — just the chat/generate route region, bounded
sp = os.path.join(VIN, "server.py")
if os.path.isfile(sp):
    L = open(sp, encoding="utf-8", errors="ignore").read().split("\n")
    print("\n===== server.py (chat/generate routes only) =====")
    for i, l in enumerate(L):
        if re.search(r'@app\.(post|get|route).*(chat|message|generate|full)|def .*(chat|message|generate)_', l, re.I):
            print("    %4d: %s" % (i + 1, l.strip()[:96]))

print("\n(READ-ONLY. Locates the assembled-context var + response point for a shadow, log-only reconsideration.)")
