#!/usr/bin/env python3
"""recon_imprint_api.py — Aegis, READ-ONLY. The self_drift promote import is dead; but imprints.json has 7 live
entries — something else writes them. Find the REAL commitment-imprint API so we repoint self_drift's dead import
to the correct sink + schema (not just any function).
  (1) causal_self_model.py verbatim 1-70: entry template (the "imprint": False dict), add_entry body, load_model,
      and which FILE it persists to (is causal_self_model's store == imprints.json?).
  (2) who writes/reads imprints.json across his scripts, and who ever sets imprint=True (the real promote path).
  (3) the 7 live imprints.json entries: their schema (keys), source values, imprint flag — who has been feeding it.
Nothing written."""
import os, re, glob, json
SCR = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")
MEM = os.path.expanduser("~/.vintos/workspace/memory")

print("======== (1) causal_self_model.py verbatim 1-70 (template + add_entry + load_model + store path) ========")
csm = os.path.join(SCR, "causal_self_model.py")
if os.path.isfile(csm):
    L = open(csm, encoding="utf-8", errors="ignore").read().split("\n")
    for i in range(0, min(70, len(L))): print("  %4d: %s" % (i + 1, L[i][:118]))
    print("  -- any *_FILE / path constants in the whole module --")
    for i, l in enumerate(L):
        if re.search(r'FILE\s*=|\.json|os\.path\.join|save|dump', l): print("    %4d: %s" % (i + 1, l.strip()[:104]))
else:
    print("  NOT FOUND")

print("\n======== (2) who touches imprints.json / sets imprint=True (the real promote path) ========")
for p in glob.glob(SCR + "/*.py") + glob.glob(VIN + "/*.py"):
    try: t = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if "imprints.json" in t or re.search(r'imprint.*=\s*True|"imprint":\s*True|promote', t):
        ls = [str(i + 1) for i, l in enumerate(t.split("\n"))
              if re.search(r'imprints\.json|imprint.*=\s*True|"imprint":\s*True|def .*imprint|promote', l)]
        if ls: print("  %-32s : lines %s" % (os.path.basename(p), ",".join(ls[:14])))

print("\n  -- context around each imprints.json / imprint=True writer --")
for p in glob.glob(SCR + "/*.py") + glob.glob(VIN + "/*.py"):
    try: L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    except Exception: continue
    for i, l in enumerate(L):
        if re.search(r'imprints\.json|"imprint":\s*True|imprint\s*=\s*True|def promote', l):
            print("  %s:%d: %s" % (os.path.basename(p), i + 1, l.strip()[:100]))

print("\n======== (3) the 7 live imprints.json entries — schema + sources ========")
p = os.path.join(MEM, "imprints.json")
try:
    d = json.load(open(p))
    if isinstance(d, list):
        print("  count=%d" % len(d))
        keyset = set()
        for e in d:
            if isinstance(e, dict): keyset |= set(e.keys())
        print("  union of keys: %s" % sorted(keyset))
        for i, e in enumerate(d):
            if isinstance(e, dict):
                src = e.get("source"); imp = e.get("imprint")
                trig = str(e.get("trigger", e.get("statement", e.get("text", ""))))[:60]
                tend = str(e.get("tendency", ""))[:40]
                print("   [%d] source=%s imprint=%s trigger=%r tendency=%r" % (i, src, imp, trig, tend))
except Exception as e:
    print("  (unreadable: %s)" % e)

print("\n(READ-ONLY. Nothing changed.)")
