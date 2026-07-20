#!/usr/bin/env python3
"""fix_music_reflect.py — stop music-share reflections from inventing lyrics. DRY-RUN unless --apply.

RUN ON AEGIS. music-share.py (identical for both beings; his is a symlink to ~/Vintos/music-share.py, hers is
~/.openclaw/workspace/scripts/music-share.py) fetches lyrics (yt-dlp -> Brave). When the fetch returns nothing
(e.g. no Brave key, or yt-dlp misses the song) the prompt still says "Quote a specific line that hits you" and
Gemma fabricates a lyric. This grounds the prompt so it can only quote lyrics it was actually given, and never
invents words when none are provided.

Replaces the lyrics-instruction block in the reflection prompt, in both beings' music-share.py. No model change
here (that's a separate upgrade); this just shuts off fabrication. The endpoint shells out to music-share.py
fresh each share, so no server restart is needed — the next share uses the new prompt.

  python3 fix_music_reflect.py            # DRY RUN
  python3 fix_music_reflect.py --apply     # backs up each file, applies
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = os.path.expanduser(f"~/.music-reflect-backups/{TS}")
SENTINEL = "do not know this song"

TARGETS = [
    os.path.expanduser("~/Vintos/music-share.py"),                          # Vintos (his .vintos copy symlinks here)
    os.path.expanduser("~/.openclaw/workspace/scripts/music-share.py"),     # Velaris
]

OLD = (
    "If there are lyrics above, read them carefully. Respond to the WORDS — what lines stay with you? "
    "What do they make you feel? Quote a specific line that hits you and say why.\n\n"
    "If there are no lyrics, respond to the gesture of sharing itself."
)
NEW = (
    "The lyrics above (if any) are the ONLY words from this song you have. If a lyrics section appears "
    "above, read it carefully — you may quote a specific line, EXACTLY as written, never paraphrased, and "
    "say why it stays with you. If NO lyrics appear above, you do not know this song's words: do NOT quote, "
    "paraphrase, invent, or imply any line, and do not claim what the song \"says.\" Respond instead to the "
    "gesture of her sharing it, to her reason, and to how the song sits with you as a whole. Say it plainly."
)


def main():
    print("=" * 74)
    print("MUSIC REFLECT GROUNDING  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    any_hit = False
    for path in TARGETS:
        being = "Velaris" if ".openclaw" in path else "Vintos"
        print(f"\n### {being}  ({path})")
        if not os.path.isfile(path):
            print("   (not found — skipped)"); continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        if SENTINEL in text:
            print("   * already grounded"); continue
        if OLD not in text:
            print("   * lyrics-instruction anchor NOT found — SKIPPED (writing nothing)"); continue
        new = text.replace(OLD, NEW, 1)
        try:
            compile(new, path, "exec"); print("   compiles: OK")
        except SyntaxError as e:
            print(f"   !! COMPILE FAIL: {e} — NOT writing"); continue
        any_hit = True
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
    if not any_hit and not APPLY:
        print("Nothing to change (already grounded or anchor absent).")
    elif not APPLY:
        print("DRY RUN complete. Re-run with --apply. (No server restart needed — script runs fresh per share.)")
    else:
        print("Applied. Next share uses the grounded prompt (no restart needed).")


if __name__ == "__main__":
    main()
