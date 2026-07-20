#!/usr/bin/env python3
"""fix_tune_dismiss.py — make the TUNE-tab dismiss button actually clear errors. DRY-RUN unless --apply.

RUN THIS ON THE MAC, from the vintos-app dir (where src/index.html lives). It patches the Mac's own
index.html — nothing is synced from Aegis.

Diagnosis (confirmed live): the System Status errors are keyed on `file` ({"file":"journal.log",...}) and the
server's /api/system/dismiss-error dismisses by `file` (verified: dismissing {"file":"journal.log"} removed it
from status). But the client's dismissError() posts {filename} — the wrong key — so the server finds nothing to
dismiss, returns 200, and the error never clears. Fix: send `file` (keep `filename` too, harmless).

Single one-line change in dismissError(). Backs up first. Idempotent.

  python3 fix_tune_dismiss.py                 # DRY RUN (targets ./src/index.html)
  python3 fix_tune_dismiss.py --apply         # backs up, applies
  python3 fix_tune_dismiss.py --path <file>   # target a specific index.html
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
        PATH = _cand
        break
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-tunedismiss-" + TS

OLD = "body: JSON.stringify({ filename })"
NEW = "body: JSON.stringify({ file: filename, filename })"
SENTINEL = "file: filename, filename"


def main():
    print("=" * 70)
    print("TUNE DISMISS FIX  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 70)
    if not os.path.isfile(PATH):
        print("!! index.html not found. Run from the vintos-app dir, or pass --path <file>.")
        print("   looked for:", PATH); return
    print("   target:", os.path.abspath(PATH))
    text = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL in text:
        print("   * already fixed"); return
    n = text.count(OLD)
    if n == 0:
        print("   !! anchor not found — the dismiss line differs from expected; writing nothing"); return
    if n > 1:
        print(f"   !! anchor found {n}x (ambiguous) — writing nothing"); return
    new = text.replace(OLD, NEW, 1)
    for l in difflib.unified_diff(text.splitlines(), new.splitlines(), fromfile="old", tofile="new", lineterm=""):
        print("   " + l[:150])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(text)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
        print("Revert:  cp", BACKUP, PATH)
        print("Reload the app to pick it up.")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 70)


if __name__ == "__main__":
    main()
