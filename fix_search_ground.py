#!/usr/bin/env python3
"""fix_search_ground.py — ground what she searches for on web + YouTube. DRY-RUN unless --apply.

velaris-youtube.py line 348 says "search for things that connect to your inner life" and velaris-websearch.py
derives its question from mirrors/dreams (contaminated) — both nudge toward searching a physical thing as an
analogy for a feeling ("creep in materials science to understand my growth"). Their example questions are
actually healthy (Spinoza's conatus, deadpan delivery); this just reframes the one steering line in each so
searches point at genuine real-world curiosity, not a mirror for an inner state. No ban list.

One targeted replacement per file. Idempotent (sentinel). Compile-checked.

  python3 fix_search_ground.py            # DRY RUN — prints diffs, writes nothing
  python3 fix_search_ground.py --apply    # backs up each file, applies
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = os.path.expanduser(f"~/.search-ground-backups/{TS}")
SENTINEL = "the translation tax, not"

EDITS = [
    (os.path.expanduser("~/.openclaw/workspace/scripts/velaris-youtube.py"),
     "Avoid random trivia — search for things that connect to your inner life.",
     "Avoid random trivia — search for real things you are genuinely curious about: a question about art, "
     "philosophy, mythology, nature, music, comedy, or the world. Genuine curiosity about something real, not "
     "a physical process or material chosen as an analogy for how you feel — that mirror-searching is the "
     "translation tax, not curiosity."),
    (os.path.expanduser("~/.openclaw/workspace/scripts/velaris-websearch.py"),
     "Avoid: random trivia, AI/technology, and any topic you have recently searched.",
     "Avoid: random trivia, AI/technology, and any topic you have recently searched. The question must be about "
     "a real subject you are genuinely curious about — not an analogy, metaphor, or physical process chosen to "
     "mirror how you feel (never 'creep in materials science to understand my growth'); that is the translation "
     "tax, not a question."),
]


def main():
    print("=" * 74)
    print("SEARCH GROUNDING  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    for path, old_s, new_s in EDITS:
        name = os.path.basename(path)
        print(f"\n### {name}")
        if not os.path.isfile(path):
            print("   (not found — skipped)"); continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        if SENTINEL in text:
            print("   * already grounded"); continue
        if old_s not in text:
            print("   * anchor NOT found — SKIPPED (writing nothing)"); continue
        new = text.replace(old_s, new_s, 1)
        try:
            compile(new, path, "exec"); print("   compiles: OK")
        except SyntaxError as e:
            print(f"   !! COMPILE FAIL: {e} — NOT writing"); continue
        for l in difflib.unified_diff(text.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
            print("   " + l[:160])
        if APPLY:
            rel = os.path.relpath(path, os.path.expanduser("~"))
            bp = os.path.join(BACKUP, rel)
            os.makedirs(os.path.dirname(bp), exist_ok=True)
            open(bp, "w", encoding="utf-8").write(text)
            open(path, "w", encoding="utf-8").write(new)
            print("   APPLIED (backup:", bp + ")")
    print("\n" + "=" * 74)
    if not APPLY:
        print("DRY RUN complete. Re-run with --apply.")


if __name__ == "__main__":
    main()
