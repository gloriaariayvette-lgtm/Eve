#!/usr/bin/env python3
"""recon_dead_import.py — Aegis, READ-ONLY. self_drift imports `promote_to_commitment_imprint` from
causal_self_model inside a bare try/except: pass. Recon couldn't find that def — so promotion may have been a
silent no-op for a long time (his behavioral drift never forming commitment imprints). Find the truth:
  (1) Does `def promote_to_commitment_imprint` exist ANYWHERE in his scripts? If not, what is the real imprint API?
  (2) causal_self_model.py: all def signatures + how imprints are actually created/stored.
  (3) LIVE TEST: actually try the exact import self_drift does, and report the real error (or success).
  (4) Is there a commitment-imprints store on disk, and does it have any entries (has promotion EVER worked)?
Nothing written."""
import os, re, sys, glob, importlib, json
SCR = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")

print("======== (1) does `def promote_to_commitment_imprint` exist anywhere in his scripts? ========")
found_any = False
for p in glob.glob(SCR + "/*.py") + glob.glob(os.path.expanduser("~/Vintos") + "/*.py"):
    try: t = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    for i, l in enumerate(t.split("\n")):
        if re.search(r'def\s+promote_to_commitment_imprint', l):
            print("  FOUND: %s:%d  %s" % (os.path.basename(p), i + 1, l.strip()[:100])); found_any = True
if not found_any:
    print("  (no def promote_to_commitment_imprint found — the import self_drift uses is DEAD)")

print("\n======== (2) causal_self_model.py — all def signatures + imprint machinery ========")
csm = os.path.join(SCR, "causal_self_model.py")
if os.path.isfile(csm):
    L = open(csm, encoding="utf-8", errors="ignore").read().split("\n")
    print("  -- def signatures --")
    for i, l in enumerate(L):
        if re.match(r'\s*def\s', l): print("    %4d: %s" % (i + 1, l.strip()[:104]))
    print("  -- lines mentioning imprint / commitment / promote --")
    for i, l in enumerate(L):
        if re.search(r'imprint|commitment|promote', l, re.I): print("    %4d: %s" % (i + 1, l.strip()[:104]))
else:
    print("  causal_self_model.py NOT FOUND at %s" % csm)

print("\n======== (3) LIVE TEST — reproduce exactly what self_drift does ========")
sys.path.insert(0, SCR)
try:
    m = importlib.import_module("causal_self_model")
    print("  import causal_self_model: OK")
    has = hasattr(m, "promote_to_commitment_imprint")
    print("  hasattr promote_to_commitment_imprint: %s" % has)
    # what imprint-ish callables DOES it expose?
    cand = [n for n in dir(m) if re.search(r'imprint|commit|promote|record|add', n, re.I) and callable(getattr(m, n))]
    print("  imprint-ish callables it DOES expose: %s" % (cand or "none"))
except Exception as e:
    print("  import causal_self_model FAILED: %r" % e)

print("\n======== (4) commitment-imprints on disk — has promotion EVER produced anything? ========")
hits = []
for p in glob.glob(MEM + "/*"):
    b = os.path.basename(p).lower()
    if re.search(r'imprint|commitment|causal.*self|self.*model', b): hits.append(p)
if not hits:
    print("  (no imprint/commitment store file found in memory/)")
for p in hits:
    try:
        d = json.load(open(p))
        if isinstance(d, dict):
            n = len(d.get("imprints", d.get("commitments", d)))
            print("  %s :: dict keys=%s  (imprints/commitments count~%s)" % (os.path.basename(p), list(d.keys())[:10], n))
        elif isinstance(d, list):
            print("  %s :: list len=%d" % (os.path.basename(p), len(d)))
    except Exception:
        sz = os.path.getsize(p)
        print("  %s :: (non-json or unreadable, %d bytes)" % (os.path.basename(p), sz))

print("\n(READ-ONLY. Nothing changed.)")
