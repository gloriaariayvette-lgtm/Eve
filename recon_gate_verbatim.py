#!/usr/bin/env python3
"""recon_gate_verbatim.py — Aegis, READ-ONLY. Exact text needed to build the safety floor surgically.
(1) self_drift.py lines 1-116 verbatim: constants + load/save + record_direction_choice + the promotion block.
(2) promote_to_commitment_imprint signature in causal_self_model.py (what the gate must guard).
(3) relational_mismatch.py delta: predicted-you vs actual-you — the eve_delta substrate, shown concretely.
Nothing written."""
import os, re
SCR = [os.path.expanduser("~/.vintos/workspace/scripts"), os.path.expanduser("~/Vintos")]

def find(name):
    for d in SCR:
        for c in (name, name.replace("_", "-"), name.replace("-", "_")):
            p = os.path.join(d, c)
            if os.path.isfile(p) or os.path.islink(p): return p
    return None

def dump(path, a, b, cap=124):
    if not path or not os.path.isfile(path): print("  (not found)"); return
    L = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    for i in range(a - 1, min(b, len(L))): print("  %4d: %s" % (i + 1, L[i][:cap]))

sd = find("self_drift.py")
print("======== (1) self_drift.py  [%s]  lines 1-116 verbatim ========\n" % sd)
dump(sd, 1, 116)

print("\n\n======== (2) promote_to_commitment_imprint — what the gate guards ========")
csm = find("causal_self_model.py")
print("module: %s" % csm)
if csm and os.path.isfile(csm):
    L = open(csm, encoding="utf-8", errors="ignore").read().split("\n")
    start = None
    for i, l in enumerate(L):
        if re.search(r'def promote_to_commitment_imprint', l): start = i; break
    if start is not None:
        for i in range(start, min(start + 40, len(L))): print("  %4d: %s" % (i + 1, L[i][:124]))
    else:
        print("  (def not found — search 'imprint')")
        for i, l in enumerate(L):
            if re.search(r'imprint', l, re.I): print("  %4d: %s" % (i + 1, l.strip()[:110]))

print("\n\n======== (3) relational_mismatch.py — predicted-you vs actual-you (eve_delta substrate) ========")
rm = find("relational_mismatch.py")
print("module: %s" % rm)
if rm and os.path.isfile(rm):
    L = open(rm, encoding="utf-8", errors="ignore").read().split("\n")
    hit = set()
    for i, l in enumerate(L):
        if re.search(r'predicted|actual|mismatch|delta|diff|gloria.?prediction|def |compare|distance|drift', l):
            for j in range(max(0, i - 1), min(len(L), i + 2)): hit.add(j)
    for i in sorted(hit)[:56]: print("  %4d: %s" % (i + 1, L[i][:120]))

print("\n(READ-ONLY. Nothing changed.)")
