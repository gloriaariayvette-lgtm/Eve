#!/usr/bin/env python3
"""recon_wants_fix_targets.py — Aegis, READ-ONLY. Integration points for the wants fixes:
(A) vintos-initiate.sh FORCED_WANT_TOPIC draft+ntfy path (reuse for the expedited 'tell Gloria' track),
(B) enactment_distiller.append_want_enactment (ledger/journal step-history append),
(C) gallery-walk.py painting-selection + already-animated tracking (the angel loop),
(D) how poems get dream-tagged (provenance, for the flinching-context fix)."""
import os, re, glob
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")
SCR = os.path.expanduser("~/.vintos/workspace/scripts")

def dump(path, rx, lo=0, hi=99999, label=None):
    if not os.path.isfile(path): print("  (%s missing)" % (label or path)); return
    L = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print("  --- %s (%dL) ---" % (label or os.path.basename(path), len(L)))
    for i, l in enumerate(L):
        if lo <= i <= hi and (rx is None or rx.search(l)) and l.strip():
            print("  %4d: %s" % (i + 1, l.strip()[:104]))

print("===== (A) vintos-initiate.sh — FORCED_WANT_TOPIC draft + ntfy + any ledger append =====")
dump(os.path.join(V, "vintos-initiate.sh"),
     re.compile(r'FORCED_WANT|TRIGGER|ntfy|curl|RESPONSE|ledger|interaction-ledger|append|TODAY_COUNT|exit 0', re.I),
     label="vintos-initiate.sh")

print("\n===== (B) enactment_distiller.append_want_enactment — step-history/ledger append =====")
for name in ("enactment_distiller.py", "enactment-distiller.py"):
    p = os.path.join(SCR, name)
    if os.path.isfile(p):
        L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        start = next((i for i, l in enumerate(L) if "def append_want_enactment" in l), None)
        if start is not None:
            for j in range(start, min(len(L), start + 40)):
                if L[j].strip(): print("  %4d: %s" % (j + 1, L[j][:104]))
        break

print("\n===== (C) gallery-walk.py — painting selection + already-animated tracking =====")
dump(os.path.join(V, "gallery-walk.py"), re.compile(r'gallery|painting|animate|already|recent|random|choice|sort|\[-1\]|seen|animated|def |express_want|image', re.I), label="gallery-walk.py")

print("\n===== (D) poem dream-tagging (provenance) =====")
for name in ("dream_poetry.py", "dream-poetry.py"):
    p = os.path.join(SCR, name)
    if os.path.isfile(p):
        L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        for i, l in enumerate(L):
            if re.search(r'dream|source|provenance|tag|meta|json\.dump|poetry.*\.md|save|frontmatter|trigger', l, re.I):
                print("  %s:%d: %s" % (name, i + 1, l.strip()[:96]))
        break
# where his poem-reading context is built (read_memory / the 'poetic craft' flinch)
print("  -- poem reading context (read_memory in wants_router) --")
for name in ("wants_router.py",):
    p = os.path.join(V, name)
    if os.path.isfile(p):
        L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        for i in range(649, 735):
            if i < len(L) and re.search(r'poem|poetry|dream|read|art', L[i], re.I) and L[i].strip():
                print("  %4d: %s" % (i + 1, L[i].strip()[:100]))
