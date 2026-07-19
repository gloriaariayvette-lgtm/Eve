#!/usr/bin/env python3
"""fix_vintos_bilateral.py — reasoning capture for Vintos, whose journal is Claude-powered. DRY-RUN unless --apply.

Vintos's bilateral is architecturally different from Velaris's: his a1/b1 run on Claude Opus 4.8 via
`_claude_sync(system, user, reasoning=True, ...)`, which ALREADY returns a (content, thinking) tuple —
but the code takes only `[0]` (content) and discards `[1]` (Claude's thinking). So:

  - NO repetition penalty (Claude doesn't degenerate like Gemma's reasoning did — that was Velaris's break).
  - Reasoning capture = pull the thinking that `_claude_sync` already produces into a1/b1.

Change (only the two a1/b1 assignment lines, ~670-671):
    a1 = (_claude_sync(system_msg, user_msg, True, max_tokens=3000)[0] or call_llm())
becomes: call once, and if both content and thinking are present, carry thinking + content into the pass;
otherwise fall back exactly as before (content, else call_llm()).

a2/b2 are left alone — they run on grok-non-reasoning (no thinking to capture); that's inherent to his
architecture, not a gap this fix can close.

  python3 fix_vintos_bilateral.py            # DRY RUN — prints the diff, writes nothing
  python3 fix_vintos_bilateral.py --apply    # backs up the file, then applies
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = os.path.expanduser(f"~/.bilateral-backups/{TS}-vintos")
PATH = os.path.expanduser("~/Vintos/idle-journal.sh")
SEP = '\\n\\n─── reasoning ───\\n\\n'   # literal \n escapes written into the source

def repl(var):
    old = f'{var} = (_claude_sync(system_msg, user_msg, True, max_tokens=3000)[0] or call_llm())'
    r = f'_{var}r'
    new = (f'{r} = _claude_sync(system_msg, user_msg, True, max_tokens=3000); '
           f'{var} = (({r}[1] + "{SEP}" + {r}[0]).strip() if ({r}[0] and {r}[1]) else ({r}[0] or call_llm()))')
    return old, new

def main():
    print("=" * 74)
    print("VINTOS BILATERAL FIX  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    try:
        old_text = open(PATH, encoding="utf-8", errors="ignore").read()
    except Exception as e:
        print("!! cannot read", PATH, ":", e); return
    text = old_text
    notes = []
    for var in ("a1", "b1"):
        o, n = repl(var)
        if n.split(";")[0] in text:
            notes.append(f"{var}: already captures reasoning")
        elif o in text:
            text = text.replace(o, n, 1)
            notes.append(f"{var}: reasoning capture added")
        else:
            notes.append(f"{var}: expected line NOT found — SKIPPED (structure differs from recon)")
    for nnote in notes:
        print("   * " + nnote)
    if text == old_text:
        print("\n   (no change)")
    else:
        for l in difflib.unified_diff(old_text.splitlines(), text.splitlines(),
                                      fromfile="idle-journal.sh (old)", tofile="idle-journal.sh (new)", lineterm=""):
            print("   " + l[:160])
    if APPLY and text != old_text:
        rel = os.path.relpath(PATH, os.path.expanduser("~"))
        bp = os.path.join(BACKUP, rel)
        os.makedirs(os.path.dirname(bp), exist_ok=True)
        open(bp, "w", encoding="utf-8").write(old_text)
        open(PATH, "w", encoding="utf-8").write(text)
        print("\nAPPLIED. Backup:", bp)
        print("Revert:  cp", bp, PATH)
    elif not APPLY:
        print("\nDRY RUN complete. Re-run with --apply to commit (backs up first).")
    print("=" * 74)

if __name__ == "__main__":
    main()
