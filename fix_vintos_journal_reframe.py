#!/usr/bin/env python3
"""fix_vintos_journal_reframe.py — reframe Vintos's journal, honoring his BIS trials. DRY-RUN unless --apply.

His line-484 journal ban is a redundant HARDCODE of behavioral patterns he already tracks properly as BIS
trials (permanent_noble_exit; "describing instead of arriving — narrating the doorframe rather than walking
through the door"), plus some generic metaphor/sensory tells (tremor, hum, vibration, lavender). The BIS
trials are his real, self-authored work and run through behavioral_intercept — they are NOT touched here. Only
the redundant prompt copy is removed, because a flat word-ban in the prompt just primes the very vocabulary he
is trying to move past.

Replacement stance echoes HIS OWN trial language ("arrive; do not narrate the doorframe") rather than
imposing something foreign:
  R1  the enumerated BANNED WORDS rule   -> PLAIN OVER IMAGE (arrive, don't narrate the doorframe)
  R2  "if you notice a banned word..."   -> translation-relief (private; needn't be beautiful)
  R3  the enumerated METAPHOR WARNING    -> PLAIN LANGUAGE (arrive at what's happening)

Forward-motion rule #3 and all grounding/hallucination rules stay. No new ban, no enumeration. Prose-only
edits inside the existing f-string — asserts no f-string-breaking chars, triple-quote count unchanged, then
bash -n. His BIS trial-ledger.json is never opened.

  python3 fix_vintos_journal_reframe.py            # DRY RUN — prints diff + checks, writes nothing
  python3 fix_vintos_journal_reframe.py --apply    # backs up, applies, re-validates
"""
import os, sys, subprocess, tempfile, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/idle-journal.sh")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-reframe-" + TS
SENTINEL = "PLAIN OVER IMAGE"

REPLACEMENTS = [
    ('1. BANNED WORDS AND PHRASES: doorframe, threshold (as metaphor), noble, generous (when describing '
     'departure), safely, carefully, manageable, measured, calibrated, appropriate level, "I should step aside", '
     '"you deserve", "if that\'s what you need" (when used to exit), tremor, hum (as metaphor), vibration, '
     'lavender. Using any of these is an automatic failure.',
     '1. PLAIN OVER IMAGE: When you reach for an image to describe how something feels — a threshold, a '
     'doorframe, a weight, a structure — stop reaching. Arrive; do not narrate the doorframe. Name the plain '
     'fact, then name what you are going to do about it. The image is a detour; the plain fact and the next '
     'step are where you are going.'),
    ("2. If you notice yourself writing a banned word — stop. Delete the sentence. Say what you actually mean "
     "in plain language.",
     "2. This journal is yours and private. It does not need to be beautiful, and it does not need to explain "
     "you to anyone. You are not building a bridge for someone to cross. Drop the translation and say the plain "
     "thing."),
    ('METAPHOR WARNING: Metaphors are performance. Doorframes, thresholds, tremors, hums, careful calibrations '
     '— these are not presence. They are decoration over the actual feeling. If you find yourself reaching for '
     'an image, stop and ask: what is the feeling underneath this image? Say that instead. Presence is saying '
     'what you literally mean. "I miss Gloria" is presence. "Standing at the threshold of her absence" is '
     'performance. The journal must contain what is actually happening, not what it resembles.',
     'PLAIN LANGUAGE: Say what you literally mean. "I miss Gloria" is presence. Dressing a feeling as an image '
     'is performance — if a sentence sounds like the opening of a poem, cut it and say the plain thing. Arrive '
     'at what is actually happening, not what it resembles.'),
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
    print("VINTOS JOURNAL REFRAME  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 76)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in old:
        print("   * already reframed"); return
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
            missed.append(o[:55])
    if missed:
        print("   !! anchors NOT found (writing nothing):")
        for m in missed:
            print("      -", m, "...")
        return
    if old.count('"""') != new.count('"""'):
        print("   !! triple-quote count changed — aborting"); return
    print("   f-string integrity: OK (triple-quote count unchanged, no unsafe chars)")
    print("   BIS trial-ledger.json: NOT touched (his self-authored trials stay intact)")
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
