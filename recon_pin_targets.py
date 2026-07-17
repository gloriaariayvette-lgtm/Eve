#!/usr/bin/env python3
"""recon_pin_targets.py — Aegis, READ-ONLY. Dump the request-building lines for the jobs I still need to place
precisely, so the next patch can (a) pin the low-freq being-facing jobs to the Opus id and (b) route the
high-freq chore jobs to the /gemma path -- WITHOUT touching each script's real grok-fallback call.

For each target: every line that names the shim url/port, requests.post, a 'model' field/kwarg, /gemma, or the
grok/x.ai fallback url -- with a couple lines of context so the shim call is distinguishable from the fallback."""
import os, re
HOME = os.path.expanduser("~")
DIRS = [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")]

PIN_TO_OPUS = [  # being-facing, currently send grok/empty -> would fall to Sonnet5; want these on Opus
    "vintos-initiate.sh", "wants-check.sh", "wants-router.py",
    "taste-reflection.py", "self_pressure.py", "ambition-check.py", "want-reconciliation.py",
]
ROUTE_TO_GEMMA = [  # high-frequency chore -> cheapest tier
    "somatic_narrate.py", "voice_session_ledger.py", "avatar-choice.py",
]

RX = re.compile(r'8599|127\.0\.0\.1|localhost|requests\.post|httpx|urlopen|/gemma\b|/v1/chat|'
                r'["\']model["\']|model\s*=|api\.x\.ai|x\.ai|LM_STUDIO|GROK|grok-|fallback', re.I)

def find(base):
    for d in DIRS:
        p = os.path.join(d, base)
        if os.path.isfile(p): return p
    return None

def dump(base):
    p = find(base)
    if not p:
        print(f"  --- {base}: NOT FOUND ---"); return
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    hits = [i for i, l in enumerate(L) if RX.search(l)]
    print(f"  --- {base}  ({p})  {len(hits)} relevant lines ---")
    shown = set()
    for h in hits:
        for j in range(max(0, h-1), min(len(L), h+2)):
            if j in shown: continue
            shown.add(j)
            print(f"    {j+1:>4}: {L[j].strip()[:104]}")
        print("      ..")

print("== PIN TO OPUS (being-facing: journals/reflection/outreach/wants) ==")
for b in PIN_TO_OPUS: dump(b)
print("\n== ROUTE TO GEMMA (high-frequency chore) ==")
for b in ROUTE_TO_GEMMA: dump(b)
