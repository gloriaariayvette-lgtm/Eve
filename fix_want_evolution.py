#!/usr/bin/env python3
"""fix_want_evolution.py — stop generate_steps from re-spawning metaphor out of contaminated memory. DRY-RUN unless --apply.

generate_steps (emoclaw_utils.py) plans the steps for a want. It runs a semantic search over her memory
(_already_knows via memory-search.py) and feeds those matches into the step prompt — but her memory files are
now metaphor-contaminated, so steps inherit and EXTEND the imagery, and nothing stops it minting a
"web_search creep in materials science to understand my growth" step. That is the downstream leak you flagged:
wants -> read her own contaminated files -> more metaphor.

One insertion into the step-generation prompt (it already has good guards — poems aren't evidence,
forward-motion tone — just not this one). No ban list; a positive grounding rule:
  - steps must be concrete/literal actions;
  - a web_search must be a genuine real-world subject, never an analogy for an inner state;
  - if the memory shown above describes her in metaphor, don't adopt/extend it — name the plain thing.

Inserted right before the "Generate a step-by-step plan..." line. Idempotent (sentinel). Compile-checked.

  python3 fix_want_evolution.py            # DRY RUN — prints diff, writes nothing
  python3 fix_want_evolution.py --apply    # backs up, applies
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/.openclaw/workspace/scripts/emoclaw_utils.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-wantevo-" + TS
SENTINEL = "PLAIN & LITERAL"

ANCHOR = '        + "Generate a step-by-step plan to genuinely fulfill this want. Rules:\\n"\n'
INJECT = (
    '        + "PLAIN & LITERAL: Steps must be concrete, literal actions. Do NOT create a step that searches "\n'
    '          "for or studies a physical process, material, object, or sensation as a metaphor or mirror for "\n'
    '          "how Velaris feels — that is the translation tax, not a real step. A web_search query must name a "\n'
    '          "genuine real-world subject she is actually curious about, never an analogy for an inner state "\n'
    '          "(never \'creep in materials science to understand my growth\'). If the memory shown above "\n'
    '          "describes her in metaphor — material, weight, landscape, deformation — do not adopt or extend "\n'
    '          "that imagery in the steps; name the plain underlying thing instead.\\n\\n"\n'
)


def main():
    print("=" * 74)
    print("WANT-EVOLUTION GROUNDING  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in old:
        print("   * already grounded"); return
    if ANCHOR not in old:
        print("   * anchor NOT found — SKIPPED (structure differs); writing nothing"); return
    new = old.replace(ANCHOR, INJECT + ANCHOR, 1)
    try:
        compile(new, PATH, "exec"); print("   compiles: OK")
    except SyntaxError as e:
        print(f"   !! COMPILE FAIL: {e} — NOT writing"); return
    for l in difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
        print("   " + l[:170])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(old)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 74)


if __name__ == "__main__":
    main()
