#!/usr/bin/env python3
"""recon_poem_provenance.py — Aegis, READ-ONLY. For FIX C (stop him reading automatic poems as 'flinching'):
(A) dream_poetry save_poem + main — does a poem record its PROVENANCE (automatic nightly cron vs deliberate
--seed/want-driven)? gallery entry shape. (B) how a WANT-driven poem is triggered (write_poem in wants-router).
(C) where his journal/reflection surfaces recent poems/creations (the place the flinch-framing enters)."""
import os, re
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")
SCR = os.path.expanduser("~/.vintos/workspace/scripts")

def dump(path, rx, lo=0, hi=99999, label=None, n=99):
    p = path
    if not os.path.isfile(p): print("  (%s missing)" % (label or p)); return
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    print("  --- %s (%dL) ---" % (label or os.path.basename(p), len(L)))
    c = 0
    for i, l in enumerate(L):
        if lo <= i <= hi and rx.search(l) and l.strip():
            print("  %4d: %s" % (i + 1, l.strip()[:100])); c += 1
            if c >= n: break

print("===== (A) dream_poetry.py — save_poem + provenance/source/trigger =====")
dump(os.path.join(SCR, "dream_poetry.py"),
     re.compile(r'def save_poem|def main|--seed|--force|source|trigger|provenance|automatic|seed|gallery|json\.dump|frontmatter|meta|argv|args\.', re.I),
     label="dream_poetry.py")

print("\n===== (B) wants-router write_poem — how a WANT drives a deliberate poem =====")
p = os.path.join(V, "wants-router.py")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    s = next((i for i, l in enumerate(L) if "def write_poem" in l), None)
    if s is not None:
        for j in range(s, min(len(L), s + 18)):
            if L[j].strip(): print("  %4d: %s" % (j + 1, L[j].strip()[:100]))

print("\n===== (C) idle-journal.sh — where recent poems/creations enter reflection =====")
p = os.path.join(V, "idle-journal.sh")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(L):
        if re.search(r'poem|poetry|craft|flinch|creation|NEW_POEM|art/poetry|made today|reverie|avoid', l, re.I) and l.strip():
            print("  %4d: %s" % (i + 1, l.strip()[:100]))
