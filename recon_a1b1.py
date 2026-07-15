#!/usr/bin/env python3
"""recon_a1b1.py — Aegis, READ-ONLY. conflict_surface=friction, reality_ebm=synthesis — neither is a1/b1.
Find the two actual bilateral PASSES (a1/b1) and the orchestrator. Grep labels + who calls the gemma model
tagged as a pass + who imports conflict_surface/reality_ebm (the orchestrator sits just above a1/b1)."""
import os, re, glob
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
def sh(p): return p.replace(HOME, "~")
FILES = glob.glob(os.path.join(SC, "*.py")) + glob.glob(os.path.join(SC, "*.sh"))

print("===== literal a1 / b1 / pass / hemisphere labels =====")
for f in FILES:
    for i, l in enumerate(open(f, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'(["\']|_|\b)(a1|b1)(["\']|_|\b)|hemisphere\s*[ab]|pass\s*[ab1]|bilateral', l) and l.strip() \
           and not l.strip().startswith("#"):
            print(f"  {os.path.basename(f)}:{i+1}| {l.strip()[:100]}")

print("\n===== orchestrator: who imports/calls conflict_surface or reality_ebm =====")
for f in FILES:
    txt = open(f, encoding="utf-8", errors="ignore").read()
    if ("conflict_surface" in txt or "reality_ebm" in txt) and os.path.basename(f) not in ("conflict_surface.py", "reality_ebm.py"):
        for i, l in enumerate(txt.split("\n")):
            if ("conflict_surface" in l or "reality_ebm" in l) and l.strip():
                print(f"  {os.path.basename(f)}:{i+1}| {l.strip()[:100]}")
                break

print("\n===== scripts whose NAME suggests a bilateral pass, + their gemma call =====")
for f in FILES:
    b = os.path.basename(f)
    if re.search(r'bilateral|hemisphere|pass|reason|deliberat|think|reflect|synth', b, re.I):
        txt = open(f, encoding="utf-8", errors="ignore").read()
        has = 'gemma-4-12b-qat' in txt
        print(f"  {b:34} gemma-call={'YES' if has else 'no'}")
print("\n(done — point me at the two files that ARE a1 and b1)")
