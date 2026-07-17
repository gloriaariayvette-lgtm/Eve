#!/usr/bin/env python3
"""recon_velaris_errors.py — Aegis, READ-ONLY. Velaris (she/her), ~/.openclaw. Pin her two errors:
(1) [Therapy] Trial extractor failed: 'source' — KeyError in a trial extractor; (2) [Absence] Absence reinforced
on error-themed wants — where absence picks wants + whether it filters error/meta content."""
import os, re, glob
HOME = os.path.expanduser("~")
OC = os.path.join(HOME, ".openclaw/workspace/scripts")
if not os.path.isdir(OC):
    print("Velaris scripts dir not found:", OC); raise SystemExit(0)
files = glob.glob(os.path.join(OC, "*.py")) + glob.glob(os.path.join(OC, "*.sh"))

print("== (1) '[Therapy] Trial extractor' + the 'source' access ==")
for f in sorted(files):
    try: L = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    except Exception: continue
    hitlines = [i for i, l in enumerate(L) if "Trial extractor" in l or "[Therapy]" in l or re.search(r'trial.*extract|extract.*trial', l, re.I)]
    if hitlines:
        print(f"  --- {os.path.basename(f)} ---")
        for h in hitlines[:6]:
            for j in range(max(0, h-4), min(len(L), h+4)):
                if re.search(r'\[.source.\]|\.get\(.source|\bsource\b|extract|Trial|for .* in', L[j]):
                    print(f"    {j+1}: {L[j].strip()[:96]}")
            print("     --")

print("\n== (2) '[Absence] Absence reinforced' — selection + any error/meta filter ==")
for f in sorted(files):
    try: L = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    except Exception: continue
    hits = [i for i, l in enumerate(L) if "Absence reinforced" in l or "[Absence]" in l or re.search(r'def .*absence|reinforce.*absence|absence.*reinforce', l, re.I)]
    if hits:
        print(f"  --- {os.path.basename(f)} ---")
        shown = set()
        for h in hits[:8]:
            for j in range(max(0, h-6), min(len(L), h+3)):
                if j in shown: continue
                shown.add(j); print(f"    {j+1}: {L[j].strip()[:96]}")
            print("     --")
