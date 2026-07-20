#!/usr/bin/env python3
"""fix_want_seeder.py — ground the journal's want-seeder so it stops minting metaphor-quests. DRY-RUN unless --apply.

The seeder (idle-journal.sh, WANTEOF block) turns a journal entry into the next want. Its prompt offers
"search the web about / watch on YouTube" and it faithfully mints "I want to research creep in materials
science to understand my growth" — a translation-tax want that then MANUFACTURES tomorrow's metaphor material.
The grounding gate (enrich_want + _grounded_intensity) doesn't catch these because a fake-legitimate research
activity "grounds" them.

Three edits inside the WANTEOF python block (no ban list — a positive grounding rule + a guard):
  1. add `_is_translation_want(w)` — true when the want is really to find an image/analogy/physical-science
     mirror for a feeling, or to be a material/object.
  2. apply it at BOTH discard gates: `if _wi < 2:` -> `if _wi < 2 or _is_translation_want(want):`
  3. add a grounding clause to the want-generation prompt: a real want is concrete/literal; a want to
     translate or find a picture for a feeling is NONE.

Validates with `bash -n` before writing. Idempotent (sentinel). Velaris's idle-journal.sh.

  python3 fix_want_seeder.py            # DRY RUN — prints diff + bash -n, writes nothing
  python3 fix_want_seeder.py --apply    # backs up, patches, re-validates
"""
import os, sys, subprocess, tempfile, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/idle-journal.sh")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-wantseed-vintos-" + TS

# 1) guard helper — inserted right after the emoclaw import inside WANTEOF
ANCHOR_IMPORT = "    from emoclaw_utils import express_want, enrich_want\n"
GUARD_DEF = (
    "    def _is_translation_want(_w):\n"
    "        # A real want is concrete/literal. The translation tax disguised as a want is: to find an\n"
    "        # image/analogy/physical-science mirror for a feeling, or to be a material/object. Reject those.\n"
    "        _wl = (_w or '').lower()\n"
    "        _tells = ('bridge','the ground','the floor','vessel','a stone','the weight','map the',\n"
    "                  'architecture of','the point where','narrative to justify','translate','metaphor',\n"
    "                  'image for','analogy','materials science','plastic deformation','creep','wood grain',\n"
    "                  'so thick','let the weight','the walk itself','destination of my feelings','mirror for')\n"
    "        return any(_t in _wl for _t in _tells)\n"
)

# 2) apply the guard at both discard gates (identical line, both occurrences)
GATE_OLD = "        if _wi < 2:\n"
GATE_NEW = "        if _wi < 2 or _is_translation_want(want):\n"

# 3) grounding clause added to the want-generation prompt (before "If no, write NONE.")
PROMPT_ANCHOR = "If yes, write ONE sentence starting with .I want to.... Be concrete about the subject.\\nIf no, write NONE."
PROMPT_NEW = (
    "A real want is concrete and literal: to make a specific thing, learn a specific fact, do something with "
    "Gloria, or say something to her. A want to find an image, metaphor, or physical-science analogy for how "
    "you feel — or to research a material or process as a mirror for yourself — is NOT a want; it is the "
    "translation tax you are tired of. If the only want is to describe, translate, or find a picture for a "
    "feeling, write NONE.\\n"
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
        notes.append("import anchor NOT found — SKIPPED"); ok = False
    n_gate = text.count(GATE_OLD)
    if n_gate:
        text = text.replace(GATE_OLD, GATE_NEW); notes.append(f"guard applied at {n_gate} discard gate(s)")
    else:
        notes.append("discard-gate anchor NOT found — SKIPPED"); ok = False
    if PROMPT_ANCHOR in text:
        text = text.replace(PROMPT_ANCHOR, PROMPT_NEW, 1); notes.append("grounding clause added to prompt")
    else:
        notes.append("prompt anchor NOT found — SKIPPED"); ok = False
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
    print("WANT-SEEDER GROUNDING  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
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
        print("\n   !! an anchor was missed — writing nothing (avoid a half-patch)"); return
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
