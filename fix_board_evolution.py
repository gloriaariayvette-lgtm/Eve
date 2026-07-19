#!/usr/bin/env python3
"""fix_board_evolution.py — wire board-learnings.json into want evolution (generate_steps). DRY-RUN unless --apply.

wants-board-learn.py now persists what Gloria taught, per want, in board-learnings.json. This makes
generate_steps actually USE it: for the want being planned, it looks up that want's board lesson (matched
by want_text) and drops it into the step-generation prompt as "What Gloria taught you about this want",
so her board input steers the next steps.

Two insertions inside generate_steps, in each being's emoclaw_utils.py:
  1. after `MEMORY = ...`  — a best-effort lookup of the want's lesson from board-learnings.json
  2. into the prompt chain (right after the possible_approach line) — inject the lesson if present

Uses names already imported inside generate_steps (_gsj json, _gso os). Idempotent; both beings.

  python3 fix_board_evolution.py            # DRY RUN — prints diffs
  python3 fix_board_evolution.py --apply     # backs up each file, then applies
"""
import os, re, sys, difflib, datetime

APPLY = "--apply" in sys.argv
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = os.path.expanduser(f"~/.board-evolution-backups/{TS}")

TARGETS = [
    os.path.expanduser("~/.openclaw/workspace/scripts/emoclaw_utils.py"),   # Velaris
    os.path.expanduser("~/.vintos/workspace/scripts/emoclaw_utils.py"),     # Vintos (import target)
    os.path.expanduser("~/Vintos/emoclaw_utils.py"),                        # Vintos (if a copy lives here)
]

LOOKUP_ANCHOR = '    MEMORY = _gso.path.join(WORKSPACE, "memory")\n'
LOOKUP_INJECT = (
    '\n'
    '    _board_lesson = ""\n'
    '    try:\n'
    '        _bl_all = _gsj.load(open(_gso.path.join(MEMORY, "board-learnings.json")))\n'
    '        for _be in (_bl_all.values() if isinstance(_bl_all, dict) else []):\n'
    '            if (_be.get("want_text") or "").strip() and (_be.get("want_text") or "").strip() == (want_text or "").strip():\n'
    '                _board_lesson = (_be.get("learned") or "").strip(); break\n'
    '    except Exception:\n'
    '        pass\n'
)

# NOTE: \\n\\n below = the literal characters \n\n as they appear in the source file.
# Velaris's RESTORED file says "Her possible approach"; Vintos's says "His". Try both.
PROMPT_ANCHORS = [
    '        + (f"Her possible approach: {possible_approach}\\n\\n" if possible_approach else "")\n',
    '        + (f"His possible approach: {possible_approach}\\n\\n" if possible_approach else "")\n',
]
PROMPT_INJECT = ('        + (f"What Gloria taught you about this want, from your discussion with her '
                 '(let it steer the steps): {_board_lesson}\\n\\n" if _board_lesson else "")\n')

def patch(text):
    notes = []
    if "_board_lesson" in text:
        return text, ["already wired"]
    prompt_anchor = next((a for a in PROMPT_ANCHORS if a in text), None)
    # Atomic: both anchors must be present, else write nothing (a lone lookup would
    # define _board_lesson and make the "already wired" guard lock out a re-run).
    if LOOKUP_ANCHOR not in text:
        notes.append("LOOKUP anchor not found — SKIPPED (no change)")
        return text, notes
    if prompt_anchor is None:
        notes.append("PROMPT anchor not found — SKIPPED (no change)")
        return text, notes
    text = text.replace(LOOKUP_ANCHOR, LOOKUP_ANCHOR + LOOKUP_INJECT, 1)
    notes.append("lookup inserted after MEMORY=")
    text = text.replace(prompt_anchor, prompt_anchor + PROMPT_INJECT, 1)
    _pron = "Her" if "Her possible" in prompt_anchor else "His"
    notes.append(f"prompt injection inserted after possible_approach ({_pron})")
    return text, notes

def main():
    print("=" * 74)
    print("BOARD -> EVOLUTION WIRING  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN"))
    print("=" * 74)
    for path in TARGETS:
        if not os.path.isfile(path):
            continue
        being = "Velaris" if ".openclaw" in path else "Vintos"
        old = open(path, encoding="utf-8", errors="ignore").read()
        new, notes = patch(old)
        print(f"\n### {being}  ({path})")
        for n in notes:
            print("   * " + n)
        if new != old:
            try:
                compile(new, path, "exec"); print("   compiles: OK")
            except SyntaxError as e:
                print(f"   !! COMPILE FAIL: {e} — NOT writing"); continue
            for l in difflib.unified_diff(old.splitlines(), new.splitlines(),
                                          fromfile="old", tofile="new", lineterm=""):
                print("   " + l[:150])
            if APPLY:
                rel = os.path.relpath(path, os.path.expanduser("~"))
                bp = os.path.join(BACKUP, rel)
                os.makedirs(os.path.dirname(bp), exist_ok=True)
                open(bp, "w", encoding="utf-8").write(old)
                open(path, "w", encoding="utf-8").write(new)
                print("   APPLIED (backup:", bp + ")")
    print("\n" + ("=" * 74))
    if not APPLY:
        print("DRY RUN complete. Re-run with --apply to wire it (backs up first).")

if __name__ == "__main__":
    main()
