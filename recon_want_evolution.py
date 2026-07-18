#!/usr/bin/env python3
"""recon_want_evolution.py — Aegis, READ-ONLY. Find the want-EVOLUTION system and why it didn't mutate the repeated
'send the ask' want forward instead of letting 10 clones pile up. Checks: (A) what TRIGGERS evolution (fulfillment
only, or repeat-detection?), (B) grok_evolve / generate_third_order_want / spawn_echo_want bodies, (C) similarity_gate
on a near-dup — does it EVOLVE the existing want or just BLOCK/suppress?, (D) wants-check seeding (the re-seed source)."""
import os, re, glob
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")
SCR = os.path.expanduser("~/.vintos/workspace/scripts")

print("== (A) everywhere 'evolve/mutate/forward/third-order/echo' appears in the wants system ==")
rx = re.compile(r'evolve|mutat|forward|third.?order|echo.?want|advance.*want|what opens next|repeat.*want|want.*repeat|supersed', re.I)
for p in glob.glob(SCR + "/*.py") + glob.glob(V + "/*.py") + glob.glob(V + "/*.sh"):
    b = os.path.basename(p)
    if b.startswith(("recon", "port_", "patch_", "build_", "deploy_")): continue
    try: L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    except Exception: continue
    for i, l in enumerate(L):
        if rx.search(l): print("  %s:%d: %s" % (b, i + 1, l.strip()[:94]))

print("\n== (B1) want-reconciliation grok_evolve + what triggers it (fulfilled only?) ==")
p = os.path.join(V, "want-reconciliation.py")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(L):
        if re.search(r'def |fulfilled|evolve|express_want|for w in|only|trigger', l, re.I): print("  %d: %s" % (i + 1, l.strip()[:96]))

print("\n== (B2) generate_third_order_want + spawn_echo_want (emoclaw_utils) — triggers ==")
p = os.path.join(SCR, "emoclaw_utils.py")
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
for fn in ("generate_third_order_want", "spawn_echo_want"):
    start = next((i for i, l in enumerate(L) if ("def " + fn) in l), None)
    if start is not None:
        print("  --- %s (L%d) ---" % (fn, start + 1))
        for j in range(start, min(len(L), start + 22)):
            if L[j].strip(): print("  %d: %s" % (j + 1, L[j].strip()[:96]))

print("\n== (C) similarity_gate on near-dup: EVOLVE existing or just BLOCK? ==")
p = os.path.join(SCR, "similarity_gate.py")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(L):
        if re.search(r'def |threshold|block|suppress|evolve|mutat|return|similar|WANT_THRESHOLD|FULFILLED_THRESHOLD', l, re.I):
            print("  %d: %s" % (i + 1, l.strip()[:96]))

print("\n== (D) wants-check seeding — why it re-generates the same ask ==")
p = os.path.join(V, "wants-check.sh")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(L):
        if re.search(r'express_want|repeat|already|recent|dedup|similar|prompt|want_text|You want|system', l, re.I):
            print("  %d: %s" % (i + 1, l.strip()[:96]))
