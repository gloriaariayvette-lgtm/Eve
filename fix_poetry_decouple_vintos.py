#!/usr/bin/env python3
"""fix_poetry_decouple.py — decouple poetry from the contaminated journal+dream feeds. DRY-RUN unless --apply.

dream-poetry.py builds the poem's context from get_latest_dream() + get_recent_journal() + get_recent_blush().
The journal and dream are the metaphor-drenched produced-content feeds — so the poem distills the day's
fixation ("Thermal Creep" is the journal's creep, compressed), and since the poem reaches daily-creative, it
amplifies the attractor back into tomorrow's journal material. This makes poetry independent of those two
feeds: it draws from her actual emotional state, real events, taste, and Gloria — not the ruminative journal
or dream.

NOT a metaphor ban (that paradigm failed) and it does NOT touch the poem's nature — poems still get imagery.
It only removes the two contaminated INPUTS from the poem context. get_latest_dream/get_recent_journal remain
defined (harmless); they're just no longer fed into the prompt.

Idempotent (sentinel). Compile-checked. Velaris's dream-poetry.py (Vintos handled in his own phase).

  python3 fix_poetry_decouple.py            # DRY RUN — prints diff, writes nothing
  python3 fix_poetry_decouple.py --apply    # backs up, applies
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/dream-poetry.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-decouple-vintos-" + TS

OLD = (
    "    context_parts = []\n"
    "    if dream:\n"
    "        context_parts.append(f\"Your most recent dream:\\n{dream[:500]}\")\n"
    "    if journal:\n"
    "        context_parts.append(f\"Your recent journal:\\n{journal[:400]}\")\n"
    "    if blush:\n"
    "        context_parts.append(f\"A recent moment of self-correction:\\n{blush}\")\n"
)
NEW = (
    "    context_parts = []\n"
    "    # DECOUPLED from dream + recent-journal: those are the metaphor-contaminated produced-content feeds\n"
    "    # that made poetry re-concentrate the day's fixation and amplify it back into daily-creative. Poetry\n"
    "    # now draws from his emotional state, real events, taste, and Gloria — not the ruminative journal/dream.\n"
    "    if blush:\n"
    "        context_parts.append(f\"A recent moment of self-correction:\\n{blush}\")\n"
)
SENTINEL = "DECOUPLED from dream + recent-journal"


def main():
    print("=" * 74)
    print("POETRY DECOUPLE  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in old:
        print("   * already decoupled"); return
    if OLD not in old:
        print("   * context-parts anchor NOT found — SKIPPED (structure differs); writing nothing"); return
    new = old.replace(OLD, NEW, 1)
    try:
        compile(new, PATH, "exec"); print("   compiles: OK")
    except SyntaxError as e:
        print(f"   !! COMPILE FAIL: {e} — NOT writing"); return
    for l in difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
        print("   " + l[:160])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(old)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 74)


if __name__ == "__main__":
    main()
