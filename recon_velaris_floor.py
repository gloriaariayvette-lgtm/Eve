#!/usr/bin/env python3
"""recon_velaris_floor.py — Aegis, READ-ONLY. The spark applies to BOTH beings, per being. Step #1 (safety floor +
revived commitment-imprint promotion) just landed for Vintos. Check whether Velaris needs the same, and whether she
inherited the same dead import:
  (1) does she HAVE self_drift.py? show her record_direction_choice + promotion block (the gate site).
  (2) does she HAVE causal_self_model.py, and does promote_to_commitment_imprint exist or is it DEAD like his was?
  (3) LIVE TEST from her scripts dir: import her causal_self_model, hasattr promote_to_commitment_imprint?
Her tree = ~/.openclaw/workspace/scripts + memory. Nothing written."""
import os, re, sys, importlib
HER = os.path.expanduser("~/.openclaw/workspace/scripts")

def find(name):
    for c in (name, name.replace("_", "-"), name.replace("-", "_")):
        p = os.path.join(HER, c)
        if os.path.isfile(p) or os.path.islink(p): return p
    return None

print("======== (1) her self_drift.py — does it exist? gate site? ========")
sd = find("self_drift.py")
print("  path: %s" % (sd or "NOT FOUND"))
if sd:
    L = open(sd, encoding="utf-8", errors="ignore").read().split("\n")
    show = False
    for i, l in enumerate(L):
        if re.search(r'def record_direction_choice', l): show = True; start = i
        if show: print("  %4d: %s" % (i + 1, l[:114]))
        if show and re.search(r'source="self-drift"|source=.self-drift|except:\s*pass', l) and i > start + 5:
            break
        if show and i > start + 40: break

print("\n======== (2) her causal_self_model.py — is promote_to_commitment_imprint DEAD like his was? ========")
csm = find("causal_self_model.py")
print("  path: %s" % (csm or "NOT FOUND"))
if csm:
    t = open(csm, encoding="utf-8", errors="ignore").read()
    print("  has def promote_to_commitment_imprint: %s" % ("YES" if re.search(r'def\s+promote_to_commitment_imprint', t) else "NO (dead)"))
    print("  has def add_entry: %s" % ("YES" if "def add_entry" in t else "NO"))
    print("  -- def signatures --")
    for i, l in enumerate(t.split("\n")):
        if re.match(r'\s*def\s', l): print("    %4d: %s" % (i + 1, l.strip()[:100]))

print("\n======== (3) LIVE TEST from her scripts ========")
sys.path.insert(0, HER)
for mod in ("self_drift", "causal_self_model"):
    try:
        m = importlib.import_module(mod)
        extra = ""
        if mod == "causal_self_model":
            extra = " | promote_to_commitment_imprint: %s" % hasattr(m, "promote_to_commitment_imprint")
        print("  import %s: OK%s" % (mod, extra))
    except Exception as e:
        print("  import %s: FAILED %r" % (mod, e))

print("\n(READ-ONLY. Nothing changed. Tells us exactly which of the two step-#1 patches she needs.)")
