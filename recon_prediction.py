#!/usr/bin/env python3
"""recon_prediction.py — Aegis, READ-ONLY. Map the existing prediction machinery so Prediction Ledger can be
extended to the full dual self+Gloria form (predict next sentence/emotion/action/request for BOTH, grade misses
into trajectory). Finds: (A) the relational-mismatch predictor (predicts Gloria) in full, (B) the server.py:2936
'predict Gloria's reaction' block, (C) any SELF prediction already present, (D) prediction storage files + where
misses are graded / fed onward. Nothing changed."""
import os, re, glob
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")
SCR = os.path.expanduser("~/.vintos/workspace/scripts")

print("== (A) relational mismatch predictor (predicts Gloria) ==")
for cand in ("relational_mismatch.py",):
    for base in (V, SCR):
        p = os.path.join(base, cand)
        if os.path.isfile(p):
            L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
            print(f"  {p}  ({len(L)}L)")
            for i, l in enumerate(L):
                if re.search(r'def |predict|expect|mismatch|reaction|json\.dump|\.json|grade|error', l, re.I):
                    print(f"    {i+1:>4}: {l.strip()[:100]}")
            break

print("\n== (B) server.py ~2936 'predict Gloria's reaction' ==")
S = open(os.path.join(V, "server.py"), encoding="utf-8", errors="ignore").read().split("\n")
for i in range(2925, 2985):
    if i < len(S): print(f"  {i+1:>5}: {S[i].strip()[:104]}")

print("\n== (C) any SELF prediction already present ==")
for base in (V, SCR):
    for p in glob.glob(base + "/*.py"):
        t = open(p, encoding="utf-8", errors="ignore").read()
        if re.search(r'predict.{0,20}self|self.{0,20}predict|self[_-]prediction|what.{0,6}I.{0,6}(will|say)', t, re.I):
            b = os.path.basename(p)
            for i, l in enumerate(t.split("\n")):
                if re.search(r'predict.{0,20}self|self.{0,20}predict|self[_-]prediction', l, re.I):
                    print(f"    {b}:{i+1}: {l.strip()[:96]}")

print("\n== (D) prediction storage files + grading/feeding ==")
for base in (V, SCR):
    for p in glob.glob(base + "/*.py"):
        t = open(p, encoding="utf-8", errors="ignore").read()
        for i, l in enumerate(t.split("\n")):
            if re.search(r'prediction.*\.json|ledger.*\.json|predictions\.json|graded|miss.*(causal|trajectory)|prediction[_-]ledger', l, re.I):
                print(f"    {os.path.basename(p)}:{i+1}: {l.strip()[:96]}")
