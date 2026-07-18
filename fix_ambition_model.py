#!/usr/bin/env python3
"""fix_ambition_model.py — Aegis. The Velaris ambition-check port swapped the note endpoint (his 8599 shim) to her
Gemma URL but left GROK_MODEL as a grok model her LM Studio doesn't serve — so grok_note() fails and the completion
note silently degrades to raw evidence. Point the note model at her Gemma so the warm note actually generates.
Backup + compile-check. --apply to commit (safe one-line change)."""
import os, sys, time, shutil

APPLY = "--apply" in sys.argv
P = os.path.expanduser("~/.openclaw/workspace/scripts/ambition-check.py")
OLD = 'GROK_MODEL = "grok-4.20-0309-non-reasoning"'
NEW = 'GROK_MODEL = "google/gemma-4-12b-qat"'

if not os.path.isfile(P):
    print("!! her ambition-check.py not found"); sys.exit(1)
txt = open(P, encoding="utf-8").read()
print("================  fix ambition note model  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
if NEW in txt and OLD not in txt:
    print("already fixed."); sys.exit(0)
n = txt.count(OLD)
print("anchor '%s' x%d (want 1)" % (OLD, n))
if n != 1:
    print("!! anchor not unique — aborting"); sys.exit(1)
new = txt.replace(OLD, NEW)
try: compile(new, P, "exec"); print("  note model -> her Gemma (compiles OK)")
except SyntaxError as e: print("  !! would not compile: %s" % e); sys.exit(1)
if not APPLY:
    print("\n(DRY-RUN — nothing written.)"); sys.exit(0)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
print("\npatched %s (backup %s). Her completion notes now generate on Gemma." % (P, bak))
