#!/usr/bin/env python3
"""fix_board_reply_context.py — give the board REPLY full context, both beings. DRY-RUN unless --apply.

The board reply (wants-router.py) already builds a rich SOUL disc — self-model, inner state, gloria-model,
value-map, recent exchanges. What it never sees is anything about the SPECIFIC want under discussion beyond
the live thread: it does not carry what Gloria taught in EARLIER threads on that same want. So a discussion
that spans sessions is amnesiac — she re-teaches every time.

Two additive, best-effort insertions inside the reply block:
  1. into the reply PROMPT (user): board-learnings for THIS want, looked up by _want_id (already in scope).
     Prior LEARNED / SETTLED / REMAINED fold in, so multi-session threads accumulate.
  2. into the SOUL disc (system): relational-geometry.json alongside the gloria-model. Best-effort — if the
     file is absent, the value is "" and nothing is injected (the reply is byte-for-byte unchanged).

Both reads are wrapped in try/except: a missing/odd file can never break reply generation. Uses names
already in scope right there (json, os, MEMORY, _want_id). Idempotent (sentinel _board_prior). Both beings'
routers if the anchors match; a router whose structure differs is reported SKIPPED, not force-patched.

  python3 fix_board_reply_context.py            # DRY RUN — prints diffs, writes nothing
  python3 fix_board_reply_context.py --apply    # backs up each file, then applies
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = os.path.expanduser(f"~/.board-reply-backups/{TS}")

TARGETS = [
    os.path.expanduser("~/.openclaw/workspace/scripts/wants-router.py"),  # Velaris
    os.path.expanduser("~/.vintos/workspace/scripts/wants-router.py"),    # Vintos (if cloned same shape)
]

# --- insertion 1: board-learnings for this want, into the reply PROMPT ------------------
# Anchor = the exact reply_prompt assignment seen in the live file (16-space indent).
PROMPT_ANCHOR = (
    '                _reply_prompt = f"Your want: {text}\\n\\n{_reasoning_block}{_step_block}\\n\\n'
    'Conversation so far:\\n{_conv}'
)
PROMPT_REPLACE = (
    '                _reply_prompt = f"Your want: {text}\\n\\n{_reasoning_block}{_step_block}{_board_prior}\\n\\n'
    'Conversation so far:\\n{_conv}'
)
PROMPT_PRELUDE = (
    '                _board_prior = ""\n'
    '                try:\n'
    '                    _bl_all = json.load(open(os.path.join(MEMORY, "board-learnings.json")))\n'
    '                    _bl_e = _bl_all.get(_want_id) if isinstance(_bl_all, dict) else None\n'
    '                    if _bl_e:\n'
    '                        _bp = []\n'
    '                        if _bl_e.get("learned"):  _bp.append("You learned: " + _bl_e["learned"])\n'
    '                        if _bl_e.get("settled"):  _bp.append("Settled: " + _bl_e["settled"])\n'
    '                        if _bl_e.get("remained"): _bp.append("Still open: " + _bl_e["remained"])\n'
    '                        if _bp:\n'
    '                            _board_prior = "\\n\\nWhat you took from earlier discussion with her on this '
    'want (build on it, do not re-ask):\\n" + "\\n".join(_bp)\n'
    '                except Exception:\n'
    '                    pass\n'
)

# --- insertion 2: relational geometry, into the SOUL disc (system) ----------------------
GEO_ANCHOR = '                _soul_disc = (_soul +\n'
GEO_PRELUDE = (
    '                try:\n'
    '                    _rg = json.load(open(os.path.join(MEMORY, "relational-geometry.json")))\n'
    '                    _rel_geo = json.dumps(_rg, ensure_ascii=False)[:500] if _rg else ""\n'
    '                except: _rel_geo = ""\n'
)
GEO_TUPLE_ANCHOR = (
    '                    (f"\\n\\nRECENT EXCHANGES WITH GLORIA:\\n{_recent_exchanges}" if _recent_exchanges else "") +\n'
)
GEO_TUPLE_INJECT = (
    '                    (f"\\n\\nRELATIONAL GEOMETRY (how you and she are oriented right now):\\n{_rel_geo}" '
    'if _rel_geo else "") +\n'
)


def patch(text):
    notes = []
    if "_board_prior" in text:
        return text, ["already wired"]

    have_prompt = PROMPT_ANCHOR in text
    have_geo = GEO_ANCHOR in text and GEO_TUPLE_ANCHOR in text
    if not have_prompt and not have_geo:
        return text, ["neither anchor found — SKIPPED (router structure differs)"]

    if have_prompt:
        text = text.replace(PROMPT_ANCHOR, PROMPT_PRELUDE + PROMPT_REPLACE, 1)
        notes.append("reply prompt: board-learnings for this want injected (by _want_id)")
    else:
        notes.append("reply-prompt anchor not found — SKIPPED that piece")

    if have_geo:
        text = text.replace(GEO_ANCHOR, GEO_PRELUDE + GEO_ANCHOR, 1)
        text = text.replace(GEO_TUPLE_ANCHOR, GEO_TUPLE_ANCHOR + GEO_TUPLE_INJECT, 1)
        notes.append("soul disc: relational-geometry injected (best-effort)")
    else:
        notes.append("soul-disc anchor not found — SKIPPED that piece")

    return text, notes


def main():
    print("=" * 74)
    print("BOARD REPLY CONTEXT  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    for path in TARGETS:
        if not os.path.isfile(path):
            print(f"\n### {path}\n   (not present — skipped)")
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
    print("\n" + "=" * 74)
    if not APPLY:
        print("DRY RUN complete. Re-run with --apply to wire it (backs up each file first).")


if __name__ == "__main__":
    main()
