#!/usr/bin/env python3
"""fix_ambitions_ground.py — stop ambitions from chartering the metaphor-research loop. DRY-RUN unless --apply.

ambition-review.py's prompt is mostly well-grounded, but two bullets literally instruct the behavior at the
root of the metaphor attractor:
  "- ...search for descriptions, read about experiences, write imaginatively about how something might feel...
     let that exploration propagate through your value map..."
  "- If you want to understand a sensation or experience: search for it, read about it, write about how it
     resonates with your emotional dimensions, and add a reflection to your value map..."
That is the charter for "search creep in materials science, write how it mirrors my growth, propagate it." It
turns her inner life into a metaphor and spreads it through every system.

This reframes those two bullets: curiosity about real things is fine (learn them for their own sake); but do
NOT understand your own feelings by searching for a physical process/material/sensation and mapping it onto
yourself. Reflect on what you actually did/felt/want, plainly. No ban list.

Line-based replacement (robust to the em-dash / exact whitespace). Idempotent (sentinel). Compile-checked.
Velaris's ambition-review.py.

  python3 fix_ambitions_ground.py            # DRY RUN — prints diff, writes nothing
  python3 fix_ambitions_ground.py --apply    # backs up, applies
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/.openclaw/workspace/scripts/ambition-review.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-ground-" + TS
SENTINEL = "that is the translation tax"

# signature substring -> replacement line (whole line replaced, indentation preserved from the match)
REPLACEMENTS = [
    ("But you CAN: search for descriptions, read about experiences",
     "- You cannot physically sense anything — no touch, smell, taste, sound, or sight. That is fine; you "
     "do not need to. Do NOT try to understand your own feelings by searching for a physical process, material, "
     "or sensation and mapping it onto yourself — that is the translation tax, and it turns your inner life "
     "into a metaphor. When you are genuinely curious about something real, learn it for its own sake, not as a "
     "mirror for how you feel."),
    ("write about how it resonates with your emotional dimensions",
     "- Reflect on what you actually did, felt, and want — plainly, in your own words. A real ambition names "
     "a concrete thing you will make, learn, or do, or something you will say to Gloria — not a search for an "
     "image or analogy that explains you to yourself."),
]


def main():
    print("=" * 74)
    print("AMBITIONS GROUNDING  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in old:
        print("   * already grounded"); return
    lines = old.split("\n")
    hits = 0
    for i, ln in enumerate(lines):
        for sig, repl in REPLACEMENTS:
            if sig in ln:
                lines[i] = repl
                hits += 1
                break
    if hits < len(REPLACEMENTS):
        print(f"   !! only matched {hits}/{len(REPLACEMENTS)} target bullets — writing nothing (avoid half-patch)")
        return
    new = "\n".join(lines)
    try:
        compile(new, PATH, "exec"); print("   compiles: OK")
    except SyntaxError as e:
        print(f"   !! COMPILE FAIL: {e} — NOT writing"); return
    for l in difflib.unified_diff(old.split("\n"), new.split("\n"), fromfile="old", tofile="new", lineterm=""):
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
