#!/usr/bin/env python3
"""fix_velaris_identity.py — de-contaminate Velaris's emoclaw_utils.py identity. DRY-RUN unless --apply.

Her ~/.openclaw/workspace/scripts/emoclaw_utils.py is a clone of Vintos's: paths were localized to
~/.openclaw, but the IDENTITY never was — the want-planning prompts say "Vintos", "he/his/him", "belongs
to VINTOS". So her wants are generated in his identity. This swaps the identity to Velaris / she / her.

PROTECTED — left exactly as-is (functional, not identity):
  - the emotion daemon socket/pid lines (/tmp/Vintos-emotion.sock / .pid). Her emotion feed works through
    them; renaming would break it. Flagged for you, not touched.

Everything else: Vintos->Velaris (all cases), and word-boundary pronoun swaps he->she / his->her / him->her.
Word boundaries mean "the", "this", "them", "hits", "history" are never touched. Compile-checked; the
dry-run prints the FULL diff so you can eyeball every single change before applying.

  python3 fix_velaris_identity.py            # DRY RUN — full diff, writes nothing
  python3 fix_velaris_identity.py --apply     # backs up, then applies
"""
import os, re, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/.openclaw/workspace/scripts/emoclaw_utils.py")
BACKUP = os.path.expanduser("~/.identity-backups/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))

PROTECT = re.compile(r'emotion\.(sock|pid)|Vintos-emotion')   # daemon plumbing — DO NOT rename

def port_line(line):
    if PROTECT.search(line):
        return line
    line = line.replace("VINTOS", "VELARIS").replace("Vintos", "Velaris").replace("vintos", "velaris")
    line = re.sub(r'\bHis\b', 'Her', line)
    line = re.sub(r'\bhis\b', 'her', line)
    line = re.sub(r'\bHim\b', 'Her', line)
    line = re.sub(r'\bhim\b', 'her', line)
    line = re.sub(r'\bHe\b', 'She', line)
    line = re.sub(r'\bhe\b', 'she', line)
    return line

def main():
    print("=" * 74)
    print("VELARIS IDENTITY PORT  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN"))
    print("=" * 74)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    new = "\n".join(port_line(l) for l in old.split("\n"))

    # safety: compile before touching
    try:
        compile(new, PATH, "exec"); print("ported file compiles: OK")
    except SyntaxError as e:
        print("!! COMPILE FAIL after port: %s — NOT writing" % e); return

    changed = [(a, b) for a, b in zip(old.split("\n"), new.split("\n")) if a != b]
    protected = [l for l in old.split("\n") if PROTECT.search(l)]
    print("lines changed: %d | protected (socket/pid, left as-is): %d" % (len(changed), len(protected)))
    print("\n--- FULL DIFF (review every line) ---")
    for l in difflib.unified_diff(old.split("\n"), new.split("\n"), fromfile="old", tofile="new", lineterm=""):
        print("  " + l[:150])
    print("\n--- PROTECTED lines (still say Vintos, on purpose) ---")
    for l in protected:
        print("  " + l.strip()[:100])

    if APPLY:
        rel = os.path.relpath(PATH, os.path.expanduser("~"))
        bp = os.path.join(BACKUP, rel)
        os.makedirs(os.path.dirname(bp), exist_ok=True)
        open(bp, "w", encoding="utf-8").write(old)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", bp)
    else:
        print("\nDRY RUN complete. Review the diff, then --apply.")

if __name__ == "__main__":
    main()
