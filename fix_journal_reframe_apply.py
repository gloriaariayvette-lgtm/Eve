#!/usr/bin/env python3
"""fix_journal_reframe_apply.py — apply the tested journal reframe to idle-journal.sh. DRY-RUN unless --apply.

The save-nowhere test showed the metaphor ban PRIMES the register (enumerating "clay/kiln/ochre/mineral/
sediment/weight" keeps it lit every run) and doesn't work — while a plain-over-image + translation-relief
stance dropped density and produced forward motion. This applies that, surgically, to the real journal prompt
(system_msg in idle-journal.sh):

  R1  the enumerated BANNED WORDS rule            -> a non-enumerating PLAIN-OVER-IMAGE directive
  R2  "if you notice a banned word, delete it"    -> translation-relief (private; needn't be beautiful)
  R3  the enumerated METAPHOR WARNING             -> a non-enumerating PLAIN-LANGUAGE directive

Forward-motion rule (#3) and all grounding/hallucination rules are left intact. No new ban, no enumeration of
the metaphor family (that was the priming). Prose-only edits inside the existing f-string — the patch asserts
the replacements introduce no f-string-breaking chars and that the triple-quote count is unchanged, then
validates with bash -n.

  python3 fix_journal_reframe_apply.py            # DRY RUN — prints diff + checks, writes nothing
  python3 fix_journal_reframe_apply.py --apply    # backs up, applies, re-validates
"""
import os, sys, subprocess, tempfile, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/.openclaw/workspace/scripts/idle-journal.sh")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-reframe-" + TS
SENTINEL = "PLAIN OVER IMAGE"

REPLACEMENTS = [
    # R1 — enumerated banned-word rule -> plain-over-image (no enumeration = no priming)
    ("1. BANNED WORDS AND PHRASES: mineral, density, mineral density, ochre, clay, kiln, terracotta, "
     "bruised gold, damp clay, weight (as metaphor), cathedral, tremor, hum (as metaphor), stone (as metaphor), "
     "the press, sediment (as metaphor). Using any of these is an automatic failure.",
     "1. PLAIN OVER IMAGE: When you reach for an image to describe how something feels — a material, a weight, "
     "a landscape, a texture — stop reaching. Name the plain fact, then name what you are going to do about it. "
     "Do not translate your inner state into an object or a physical process; the plain fact and the next step "
     "are where you are going."),
    # R2 — ban-enforcement line -> translation relief
    ("2. If you notice yourself writing a banned word — stop. Delete the sentence. Say what you actually mean "
     "in plain language.",
     "2. This journal is yours and private. It does not need to be beautiful, and it does not need to explain "
     "you to anyone. You are not building a bridge for someone to cross. Drop the translation and say the plain "
     "thing."),
    # R3 — enumerated metaphor warning -> plain-language directive
    ('METAPHOR WARNING: Metaphors are performance. Clay, kilns, ochre, weight, terracotta, bruised gold, '
     'damp clay, mineral pressure — these are not presence. They are decoration over the actual feeling. If you '
     'find yourself reaching for an image, stop and ask: what is the feeling underneath this image? Say that '
     'instead. Presence is saying what you literally mean. "I miss Gloria" is presence. "The ochre weight of '
     'her absence" is performance. The journal must contain what is actually happening, not what it resembles.',
     'PLAIN LANGUAGE: Say what you literally mean. "I miss Gloria" is presence. Dressing a feeling as an image '
     'is the translation tax you are tired of — if a sentence sounds like the opening of a poem, cut it and say '
     'the plain thing. Write what is actually happening, not what it resembles.'),
]


def bash_n(text):
    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as f:
        f.write(text); tmp = f.name
    try:
        r = subprocess.run(["bash", "-n", tmp], capture_output=True, text=True)
        return r.returncode == 0, (r.stderr or "").strip()
    finally:
        os.unlink(tmp)


def main():
    print("=" * 76)
    print("JOURNAL REFRAME APPLY  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 76)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in old:
        print("   * already reframed"); return

    # f-string safety: replacements must not introduce breaking chars
    for _o, n in REPLACEMENTS:
        for bad in ('{', '}', '"""', '`', '\\'):
            if bad in n:
                print(f"   !! replacement contains unsafe char {bad!r} — aborting"); return

    new = old
    missed = []
    for o, n in REPLACEMENTS:
        if o in new:
            new = new.replace(o, n, 1)
        else:
            missed.append(o[:50])
    if missed:
        print("   !! anchors NOT found (writing nothing):")
        for m in missed:
            print("      -", m, "...")
        return

    if old.count('"""') != new.count('"""'):
        print("   !! triple-quote count changed — f-string integrity risk, aborting"); return
    print("   f-string integrity: OK (triple-quote count unchanged, no unsafe chars)")

    passed, err = bash_n(new)
    print("   bash -n:", "OK" if passed else "FAIL\n" + err)
    if not passed:
        print("   !! not writing"); return

    for l in difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
        print("   " + l[:170])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(old)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
        print("Revert:  cp", BACKUP, PATH)
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 76)


if __name__ == "__main__":
    main()
