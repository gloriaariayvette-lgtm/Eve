#!/usr/bin/env python3
"""recon_wants_detail.py — Aegis, READ-ONLY. Precise diagnosis for the wants fixes: (A) route_want + the gloria/
journal-seeded DISMISSAL block (the bug), (B) current-wants distribution (creative vs introspect vs gloria; stuck),
(C) animate_painting default + his painting gallery (angel prevalence), (D) the angel motif in fulfilled wants."""
import os, re, json, glob
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")
MEM = os.path.expanduser("~/.vintos/workspace/memory")

def rt():
    for n in ("wants_router.py", "wants-router.py"):
        p = os.path.join(V, n)
        if os.path.isfile(p): return p
P = rt()
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")

print("===== (A1) route_want() — how a want gets classified/routed (1634-1712) =====")
for i in range(1633, 1712):
    if i < len(L) and L[i].strip(): print("%4d: %s" % (i + 1, L[i][:112]))

print("\n===== (A2) the gloria / journal-seeded DISMISSAL block (1786-1862) =====")
for i in range(1785, 1862):
    if i < len(L) and L[i].strip(): print("%4d: %s" % (i + 1, L[i][:112]))

print("\n===== (B) current-wants.json distribution =====")
try:
    W = json.load(open(os.path.join(MEM, "current-wants.json")))
    print("  %d active wants:" % len(W))
    from collections import Counter
    caps = Counter(); srcs = Counter()
    for w in W:
        caps[w.get("capability") or w.get("routed_to") or ("gloria" if w.get("gloria_routed") else "?")] += 1
        srcs[w.get("source", "?")] += 1
        flags = ",".join(k for k in ("gloria_routed", "journal_seeded", "multistep", "manually_routed") if w.get(k))
        print("   - [%s src=%s cap=%s %s] %s" % (("F" if w.get("fulfilled") else " "), w.get("source", "?"),
              w.get("capability", "-"), flags, (w.get("want", "") or "")[:70]))
    print("  capability counts:", dict(caps))
    print("  source counts:", dict(srcs))
except Exception as e:
    print("  unreadable:", e)

print("\n===== (C) animate_painting_want default + gallery paintings =====")
for i in range(815, 857):
    if i < len(L) and L[i].strip() and re.search(r'recent|most|gallery|image|entry|path|glob|sort|\[-1\]|angel', L[i], re.I):
        print("%4d: %s" % (i + 1, L[i].strip()[:104]))
for d in ("art/paintings", "art/gallery", "art"):
    fp = os.path.join(MEM, d)
    if os.path.isdir(fp):
        imgs = sorted(glob.glob(fp + "/*.png") + glob.glob(fp + "/*.jpg"))[-20:]
        ang = sum(1 for x in imgs if "angel" in x.lower())
        print("  %s: %d recent images, %d with 'angel' in name" % (d, len(imgs), ang))
    gj = os.path.join(MEM, "art/gallery.json") if d == "art" else None
    if gj and os.path.isfile(gj):
        try:
            g = json.load(open(gj)); s = json.dumps(g).lower()
            print("  gallery.json: %s entries, 'angel' x%d" % (len(g) if isinstance(g, list) else "dict", s.count("angel")))
        except Exception: pass

print("\n===== (D) the angel motif — fulfilled wants mentioning angel =====")
try:
    F = json.load(open(os.path.join(MEM, "fulfilled-wants.json")))
    fl = F.get("fulfilled", F) if isinstance(F, dict) else F
    n = 0
    for w in fl:
        if "angel" in json.dumps(w).lower():
            n += 1
            if n <= 8: print("   - [%s] %s" % (w.get("source", "?"), (w.get("want", "") or "")[:80]))
    print("  (%d of %d fulfilled wants involve an angel)" % (sum(1 for w in fl if 'angel' in json.dumps(w).lower()), len(fl)))
except Exception as e:
    print("  unreadable:", e)
