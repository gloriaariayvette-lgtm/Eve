#!/usr/bin/env python3
"""recon_llmcall.py — Aegis, READ-ONLY, TIGHT. (1) Is _llm_call the grok reroute/toggle path (keep grok) or a
dead/aux call (safe to move)? Show its invocations + the _draft toggle/else branch. (2) Which causality file
actually runs (cron/import), and does the underscore copy record hypotheses at all?"""
import os, re, glob
HOME = os.path.expanduser("~")
p = os.path.join(HOME, "Vintos", "server.py")
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")

print("== _llm_call invocations in chat_full_context (L2975-4308) ==")
for i in range(2974, min(len(L), 4308)):
    if "_llm_call(" in L[i] and "async def _llm_call" not in L[i]:
        print(f"  L{i+1}: {L[i].strip()[:90]}")

print("\n== _draft toggle/else branch (L3795-3840) ==")
for i in range(3794, min(len(L), 3840)):
    print(f"{i+1:>4}: {L[i][:92]}")

print("\n== how is _chat_grok / grok reroute used near here ==")
for i in range(2974, min(len(L), 4308)):
    if re.search(r'_chat_grok|force_grok|read_mode|arm_grok|reroute', L[i]):
        print(f"  L{i+1}: {L[i].strip()[:90]}")

print("\n== which causality file runs (invocations across scripts) ==")
for f in sorted(glob.glob(os.path.join(HOME, "Vintos", "*.py")) + glob.glob(os.path.join(HOME, "Vintos", "*.sh"))):
    try: t = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    for pat in ("causality-engine.py", "causality_engine", "import causality"):
        if pat in t and os.path.basename(f) not in ("causality-engine.py", "causality_engine.py"):
            for i, l in enumerate(t.split("\n")):
                if pat in l:
                    print(f"  {os.path.basename(f)} L{i+1}: {l.strip()[:80]}"); break
