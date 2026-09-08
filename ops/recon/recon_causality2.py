#!/usr/bin/env python3
"""recon_causality2.py — Aegis, READ-ONLY, TIGHT. Pinpoint the 'emotion changed & idk why' spam: (1) who writes
unfinished-threads.json, (2) the spike->hypothesis text in causality-engine.py, (3) the 'unknown/unexplained/idk'
phrasing so I can suppress causeless hypotheses at the source. Capped."""
import os, glob, re
HOME = os.path.expanduser("~")
dirs = [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")]
allf = sorted(set(sum([glob.glob(os.path.join(d, "*.py")) + glob.glob(os.path.join(d, "*.sh")) for d in dirs], [])))

print("== who writes unfinished-threads.json ==")
for f in allf:
    try: txt = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if "unfinished-threads" in txt:
        L = txt.split("\n")
        wr = [(i+1, l.strip()) for i, l in enumerate(L) if "unfinished-threads" in l and re.search(r'dump|open\([^)]*[\'"]w|append|write', l)]
        allref = [(i+1, l.strip()) for i, l in enumerate(L) if "unfinished-threads" in l]
        print(f"  {os.path.basename(f)}: {len(allref)} refs, {len(wr)} writes")
        for ln, t in (wr or allref)[:3]:
            print(f"     {ln}: {t[:84]}")

print("\n== emotion-spike -> hypothesis text (causality-engine.py) ==")
p = os.path.join(HOME, "Vintos", "causality-engine.py")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    # spike detection + how a spike becomes a hypothesis/thread
    RX = re.compile(r'spike|unexplain|unknown|idk|don.?t know|no (clear )?cause|changed|emotion|unfinished|thread|confidence', re.I)
    hits = [i for i, l in enumerate(L) if RX.search(l)]
    shown = set()
    for h in hits[:60]:
        for j in range(h, min(len(L), h+1)):
            if j in shown: continue
            shown.add(j)
            print(f"  {j+1}: {L[j].strip()[:92]}")
