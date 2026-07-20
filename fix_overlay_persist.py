#!/usr/bin/env python3
"""fix_overlay_persist.py — persist the avatar-overlay conversation across close/reopen. DRY-RUN unless --apply.

RUN ON THE MAC from the vintos-app dir. Patches the Mac's src/index.html only — nothing synced from Aegis.

_avChatHistory is initialized to [] on every load (line ~2707), so the conversation below him is blank when
you close the app and come back. This loads it from localStorage at startup and saves on every message, so
the last messages are always there.

Edits (all string-anchored, backed up, idempotent via sentinel _avSaveHistory):
  1. after the _avChatHistory=[] init: load from localStorage + define _avSaveHistory()
  2. save after each assistant push (2 sites)
  3. save after the user push in avSendChat
  4. save after the eventNote user push in _avSpeakAndShow

  python3 fix_overlay_persist.py                 # DRY RUN (targets ./src/index.html)
  python3 fix_overlay_persist.py --apply
  python3 fix_overlay_persist.py --path <file>
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = "src/index.html"
if "--path" in sys.argv:
    _i = sys.argv.index("--path")
    if _i + 1 < len(sys.argv):
        PATH = sys.argv[_i + 1]
for _cand in (PATH, "src/index.html", "index.html", os.path.expanduser("~/vintos-app/src/index.html")):
    if os.path.isfile(_cand):
        PATH = _cand; break
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-overlaypersist-" + TS
SENTINEL = "_avSaveHistory"

INIT_OLD = "let _avVrm=null,_avMixer=null,_avIdle=null,_avCurrent=null,_avClock=null,_avRenderer=null,_avScene=null,_avCamera=null,_avHand=null,_avOpen=false,_avChatHistory=[];"
INIT_NEW = (
    INIT_OLD + "\n"
    "try { _avChatHistory = JSON.parse(localStorage.getItem('_avChatHistory')||'[]') || []; } catch(e) { _avChatHistory=[]; }\n"
    "function _avSaveHistory(){ try { localStorage.setItem('_avChatHistory', JSON.stringify(_avChatHistory.slice(-60))); } catch(e){} }"
)

# (old, new, expected_count)
EDITS = [
    ("_avChatHistory.push({role:'assistant', content:raw});",
     "_avChatHistory.push({role:'assistant', content:raw}); _avSaveHistory();", 2),
    ("_avChatHistory.push({role:'user', content:text}); _avLogMsg('user', text);",
     "_avChatHistory.push({role:'user', content:text}); _avLogMsg('user', text); _avSaveHistory();", 1),
    ("_avChatHistory.push({role:'user', content:eventNote});",
     "_avChatHistory.push({role:'user', content:eventNote}); _avSaveHistory();", 1),
]


def main():
    print("=" * 70)
    print("OVERLAY PERSIST CONVERSATION  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 70)
    if not os.path.isfile(PATH):
        print("!! index.html not found. Run from vintos-app dir or pass --path."); return
    print("   target:", os.path.abspath(PATH))
    text = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in text:
        print("   * already persisted"); return
    if INIT_OLD not in text:
        print("   !! init anchor not found — writing nothing"); return
    new = text.replace(INIT_OLD, INIT_NEW, 1)
    for old, repl, want in EDITS:
        got = new.count(old)
        if got != want:
            print(f"   !! anchor count mismatch ({got} != {want}) for: {old[:50]}... — writing nothing"); return
        new = new.replace(old, repl)
    for l in difflib.unified_diff(text.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
        print("   " + l[:150])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(text)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
        print("Reload the app; the conversation below him now survives close/reopen.")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 70)


if __name__ == "__main__":
    main()
