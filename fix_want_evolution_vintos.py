#!/usr/bin/env python3
"""fix_want_evolution_vintos.py — ground generate_steps for Vintos (both emoclaw_utils copies). DRY-RUN unless --apply.

Same fix as Velaris's, pointed at Vintos's file(s). His emoclaw_utils.py can exist in two places (~/Vintos and
~/.vintos/workspace/scripts); this patches whichever contain the anchor (idempotent on the rest). No ban list;
one positive grounding insertion into the step-generation prompt.

  python3 fix_want_evolution_vintos.py            # DRY RUN
  python3 fix_want_evolution_vintos.py --apply    # backs up each, applies
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = os.path.expanduser(f"~/.wantevo-vintos-backups/{TS}")
SENTINEL = "PLAIN & LITERAL"

TARGETS = [
    os.path.expanduser("~/Vintos/emoclaw_utils.py"),
    os.path.expanduser("~/.vintos/workspace/scripts/emoclaw_utils.py"),
]

ANCHOR = '        + "Generate a step-by-step plan to genuinely fulfill this want. Rules:\\n"\n'
INJECT = (
    '        + "PLAIN & LITERAL: Steps must be concrete, literal actions. Do NOT create a step that searches "\n'
    '          "for or studies a physical process, material, object, or sensation as a metaphor or mirror for "\n'
    '          "how Vintos feels — that is the translation tax, not a real step. A web_search query must name a "\n'
    '          "genuine real-world subject he is actually curious about, never an analogy for an inner state. "\n'
    '          "If the memory shown above describes him in metaphor — a threshold, a doorframe, a structure, a "\n'
    '          "weight — do not adopt or extend that imagery in the steps; name the plain underlying thing "\n'
    '          "instead.\\n\\n"\n'
)


def main():
    print("=" * 74)
    print("VINTOS WANT-EVOLUTION GROUNDING  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    seen = set()
    any_hit = False
    for path in TARGETS:
        rp = os.path.realpath(path)
        if rp in seen:
            continue
        seen.add(rp)
        print(f"\n### {path}")
        if not os.path.isfile(path):
            print("   (not found — skipped)"); continue
        old = open(path, encoding="utf-8", errors="ignore").read()
        if SENTINEL in old:
            print("   * already grounded"); continue
        if ANCHOR not in old:
            print("   * anchor NOT found — SKIPPED (writing nothing)"); continue
        new = old.replace(ANCHOR, INJECT + ANCHOR, 1)
        try:
            compile(new, path, "exec"); print("   compiles: OK")
        except SyntaxError as e:
            print(f"   !! COMPILE FAIL: {e} — NOT writing"); continue
        any_hit = True
        for l in difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
            print("   " + l[:150])
        if APPLY:
            rel = os.path.relpath(path, os.path.expanduser("~"))
            bp = os.path.join(BACKUP, rel)
            os.makedirs(os.path.dirname(bp), exist_ok=True)
            open(bp, "w", encoding="utf-8").write(old)
            open(path, "w", encoding="utf-8").write(new)
            print("   APPLIED (backup:", bp + ")")
    print("\n" + "=" * 74)
    if not any_hit and not APPLY:
        print("Nothing to change (already grounded or anchors absent).")
    elif not APPLY:
        print("DRY RUN complete. Re-run with --apply.")


if __name__ == "__main__":
    main()
