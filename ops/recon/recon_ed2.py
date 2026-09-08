#!/usr/bin/env python3
"""recon_ed2.py — Aegis, READ-ONLY, TIGHT. The Enactment Distiller. Show (1) Vintos's ED call in idle-journal.sh,
(2) the distiller module it imports, (3) Velaris's ED as the correct reference. Only the extraction logic that
produces 'Observed capability'. Capped."""
import os, glob, re
HOME = os.path.expanduser("~")

def show(path, want_rx, ctx=4, cap=60, whole_if_small=90):
    if not os.path.isfile(path): print(f"  (missing: {path.replace(HOME,'~')})"); return
    L = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"--- {path.replace(HOME,'~')} ({len(L)} lines) ---")
    if len(L) <= whole_if_small:
        for i, l in enumerate(L): print(f"{i+1:>4}: {l[:112]}")
        return
    shown = set(); n = 0
    for i, l in enumerate(L):
        if want_rx.search(l):
            for j in range(max(0, i-ctx), min(len(L), i+ctx+1)):
                if j not in shown:
                    shown.add(j); print(f"{j+1:>4}: {L[j][:112]}"); n += 1
            print("   ..")
            if n > cap: print("   (capped)"); break

RX = re.compile(r'Observed capability|capability|enact|distill|behavior|named_without', re.I)

print("===== (1) Vintos ED call — idle-journal.sh L1195-1240 =====")
p = os.path.join(HOME, "Vintos", "idle-journal.sh")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    s = next((i for i, l in enumerate(L) if "Enactment Distiller" in l), 1194)
    for i in range(s, min(len(L), s+46)): print(f"{i+1:>4}: {L[i][:112]}")

print("\n===== (2) VINTOS distiller module (~/.vintos/workspace/scripts) =====")
for f in glob.glob(os.path.join(HOME, ".vintos/workspace/scripts", "*.py")):
    if re.search(r'enact|distill', os.path.basename(f), re.I) or "Observed capability" in open(f, errors="ignore").read():
        show(f, RX)

print("\n===== (3) VELARIS ED — the correct reference (~/.openclaw) =====")
found = False
for base in (os.path.join(HOME, ".openclaw/workspace/scripts"), os.path.join(HOME, ".openclaw")):
    for f in glob.glob(os.path.join(base, "**", "*.py"), recursive=True) + glob.glob(os.path.join(base, "**", "*.sh"), recursive=True):
        try: txt = open(f, errors="ignore").read()
        except Exception: continue
        if re.search(r'enact|distill', os.path.basename(f), re.I) or "Observed capability" in txt or "Enactment Distiller" in txt:
            show(f, RX); found = True
    if found: break
if not found: print("  (no Velaris ED found under ~/.openclaw)")
