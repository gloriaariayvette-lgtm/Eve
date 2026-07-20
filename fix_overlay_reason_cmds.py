#!/usr/bin/env python3
"""fix_overlay_reason_cmds.py — reasoning in the thought bubble + a live commands bubble on the right.

RUN ON THE MAC from vintos-app. Patches the Mac's src/index.html only. DRY-RUN unless --apply.

#2 REASONING IN THE THOUGHT BUBBLE:
  His reasoning is d.reason from /api/avatar, kept live in #avatar-reason. When the existing thought bubble
  appears (touch + audio, via _avSpeakAndShow), also show his current reasoning in it.

#3 COMMANDS BUBBLE ON THE RIGHT:
  The right-side command bubble (#av-cmd-bubble) already exists and /api/command-bubble returns real data, but
  _avCheckCommandBubble only runs once when he speaks and the bubble auto-fades in 12s — so it's never seen.
  Fix: poll it every 8s while the overlay is open (guarded to only act when visible), and remove the 12s fade
  so the last command persists on the right.

All string-anchored, backed up, idempotent.

  python3 fix_overlay_reason_cmds.py                 # DRY RUN (./src/index.html)
  python3 fix_overlay_reason_cmds.py --apply
  python3 fix_overlay_reason_cmds.py --path <file>
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
BACKUP = PATH + ".bak-overlayrc-" + TS
SENTINEL = "_avCmdPoll"

# (label, old, new, expected_count)
EDITS = [
    # #2 — reasoning into the thought bubble, right after his words are shown
    ("reasoning-in-bubble",
     "  _avShowBubble(display);",
     "  _avShowBubble(display);\n"
     "  try{ var _avr=(document.getElementById('avatar-reason')||{}).textContent||''; if(_avr) _avShowBubble(_avr); }catch(e){}",
     1),
    # #3a — poll the command bubble while overlay is open (guarded to only act when visible)
    ("commands-poll",
     "  _avPing('open');\n  _avUpdateTelemetry();\n}",
     "  _avPing('open');\n  _avUpdateTelemetry();\n"
     "  if(!window._avCmdPoll){ window._avCmdPoll = setInterval(function(){ var _ov=document.getElementById('avatar-overlay'); if(_ov && _ov.style.display!=='none') _avCheckCommandBubble(); }, 8000); }\n}",
     1),
    # #3b — stop the 12s auto-fade so the last command stays on the right
    ("commands-persist",
     "    el.style.opacity = '1';\n    setTimeout(() => { el.style.opacity = '0'; }, 12000);",
     "    el.style.opacity = '1';",
     1),
]


def main():
    print("=" * 72)
    print("OVERLAY: REASONING BUBBLE + COMMANDS BUBBLE  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 72)
    if not os.path.isfile(PATH):
        print("!! index.html not found. Run from vintos-app dir or pass --path."); return
    print("   target:", os.path.abspath(PATH))
    text = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in text:
        print("   * already applied"); return
    new = text
    for label, old, repl, want in EDITS:
        got = new.count(old)
        if got != want:
            print(f"   !! [{label}] anchor count {got} != {want} — writing nothing"); return
        new = new.replace(old, repl, 1)
        print(f"   * {label}: matched")
    for l in difflib.unified_diff(text.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
        print("   " + l[:160])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(text)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
        print("Reload the app: his reasoning shows in the thought bubble; his commands persist on the right.")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 72)


if __name__ == "__main__":
    main()
