#!/usr/bin/env python3
"""fix_want_seeder_vintos.py — ground Vintos's want-seeder. DRY-RUN unless --apply.

His seeder (in ~/Vintos/idle-journal.sh) differs from hers: no _grounded_intensity gate — it seeds at
intensity=3 directly on both the explicit and generated paths, via grok. So the guard hooks onto his two
express_want calls instead of an intensity gate:
  1. add `_is_translation_want(w)` (his register too: threshold/doorframe/cross-examine/structural/noble-exit).
  2. explicit path: discard if the extracted want is a translation-tax want.
  3. generated path: add `and not _is_translation_want(want)` to the seed condition.
  4. add the same grounding clause to the want-generation prompt.

Validates with bash -n. Idempotent (sentinel). No ban list.

  python3 fix_want_seeder_vintos.py            # DRY RUN
  python3 fix_want_seeder_vintos.py --apply    # backs up, patches, re-validates
"""
import os, sys, subprocess, tempfile, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/idle-journal.sh")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-wantseed-vintos-" + TS

ANCHOR_IMPORT = "    from emoclaw_utils import express_want, enrich_want\n"
GUARD_DEF = (
    "    def _is_translation_want(_w):\n"
    "        # A real want is concrete/literal. Translation tax disguised as a want: find an image/analogy/\n"
    "        # physical-science mirror for a feeling, or be a material/object. Includes his register.\n"
    "        _wl = (_w or '').lower()\n"
    "        _tells = ('bridge','the ground','the floor','vessel','a stone','the weight','map the',\n"
    "                  'architecture of','the point where','narrative to justify','translate','metaphor',\n"
    "                  'image for','analogy','materials science','plastic deformation','creep','wood grain',\n"
    "                  'so thick','let the weight','the walk itself','mirror for','threshold','doorframe',\n"
    "                  'cross-examin','structural shift','noble exit')\n"
    "        return any(_t in _wl for _t in _tells)\n"
)

EXPLICIT_ANCHOR = "        want = _explicit.group(0).strip()\n"
EXPLICIT_INJECT = (
    "        if _is_translation_want(want):\n"
    "            print(f\"[Journal] Want discarded — translation-tax: {want[:80]}\", file=sys.stderr); sys.exit(0)\n"
)

GEN_OLD = '    if want and want.upper() != "NONE" and want.lower().startswith("i want"):\n'
GEN_NEW = '    if want and want.upper() != "NONE" and want.lower().startswith("i want") and not _is_translation_want(want):\n'

PROMPT_ANCHOR = "If yes, write ONE sentence starting with .I want to.... Be concrete about the subject.\\nIf no, write NONE."
PROMPT_NEW = (
    "A real want is concrete and literal: to make a specific thing, learn a specific fact, do something with "
    "Gloria, or say something to her. A want to find an image, metaphor, or physical-science analogy for how "
    "you feel — or to research a material or process as a mirror for yourself — is NOT a want; it is the "
    "translation tax. If the only want is to describe, translate, or find a picture for a feeling, write NONE.\\n"
    "If yes, write ONE sentence starting with .I want to.... Be concrete about the subject.\\nIf no, write NONE."
)


def patch(text):
    notes = []
    if "_is_translation_want" in text:
        return text, ["already grounded"], True
    ok = True
    if ANCHOR_IMPORT in text:
        text = text.replace(ANCHOR_IMPORT, ANCHOR_IMPORT + GUARD_DEF, 1); notes.append("guard helper inserted")
    else:
        notes.append("import anchor NOT found"); ok = False
    if EXPLICIT_ANCHOR in text:
        text = text.replace(EXPLICIT_ANCHOR, EXPLICIT_ANCHOR + EXPLICIT_INJECT, 1); notes.append("explicit-path guard inserted")
    else:
        notes.append("explicit-path anchor NOT found"); ok = False
    if GEN_OLD in text:
        text = text.replace(GEN_OLD, GEN_NEW, 1); notes.append("generated-path guard added to condition")
    else:
        notes.append("generated-path anchor NOT found"); ok = False
    if PROMPT_ANCHOR in text:
        text = text.replace(PROMPT_ANCHOR, PROMPT_NEW, 1); notes.append("grounding clause added to prompt")
    else:
        notes.append("prompt anchor NOT found"); ok = False
    return text, notes, ok


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
    print("VINTOS WANT-SEEDER GROUNDING  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 76)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    new, notes, ok = patch(old)
    for n in notes:
        print("   * " + n)
    if new == old:
        print("\n   (no change)"); return
    if not ok:
        print("\n   !! an anchor was missed — writing nothing (avoid half-patch)"); return
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
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 76)


if __name__ == "__main__":
    main()
