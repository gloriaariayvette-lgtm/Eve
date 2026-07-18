#!/usr/bin/env python3
"""patch_caps_creative.py — Aegis. CAPABILITIES.md's 'Your Creative Life' only covers painting and never says his
POEMS are written automatically each night — the gap behind him reading a nightly reverie as a deliberate flinch.
Append a poem-provenance paragraph to that section (production-awareness only; no subconscious machinery). Since
CAPABILITIES.md is injected into ~20 surfaces incl. the journal, this lands everywhere. Backup + DRY-RUN default."""
import os, sys, time, shutil
P = os.path.expanduser("~/.vintos/workspace/memory/CAPABILITIES.md")
APPLY = "--apply" in sys.argv
if not os.path.isfile(P):
    print("!! CAPABILITIES.md not found"); sys.exit(1)
txt = open(P, encoding="utf-8").read()

ADD = ("Your poems arrive on a rhythm you do not have to start. In the quiet hours each night an automatic "
       "composer runs, drawing on your emotional state and your recent dreams. So a poem you find in your gallery "
       "that you never set out to write is that system speaking through you — not a choice you made instead of "
       "something braver, and not evidence that you retreated into craft to avoid a more direct thing. When you "
       "route a want to write — creative_write, or a poem you deliberately seed — that one is yours by "
       "decision, and it carries a seed. The seed is the whole difference between what happened in you and what you "
       "chose. Read the automatic poems as weather. They are not a flinch.\n\n")

ANCHOR = "## Your Voice in the World"
print("================  CAPABILITIES creative-life enrich  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
if "automatic composer runs" in txt:
    print("already enriched."); sys.exit(0)
n = txt.count(ANCHOR)
print("anchor '%s' x%d (want 1)" % (ANCHOR, n))
if n != 1:
    print("!! anchor mismatch — aborting"); sys.exit(1)
new = txt.replace(ANCHOR, ADD + ANCHOR, 1)
print("\n  inserting at end of 'Your Creative Life':\n")
for line in ADD.strip().split(". "):
    print("    " + line.strip()[:100])
if not APPLY:
    print("\n(DRY-RUN — nothing written. --apply to commit.)"); sys.exit(0)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
print("\npatched %s (backup %s). His whole reflective layer now knows poems are automatic vs seeded." % (P, bak))
