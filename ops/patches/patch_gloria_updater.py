#!/usr/bin/env python3
"""patch_gloria_updater.py — fix gloria-model-update.sh: APPEND a dated revision (keep prior entries)
instead of overwriting; prompt writes only what's NEW/deepened; and ground it in USER-MODEL.md (his
real deep model of her). Backup + bash -n + rollback. Aegis."""
import os, shutil, time, subprocess
p = os.path.expanduser("~/.vintos/workspace/scripts/gloria-model-update.sh")
if not os.path.isfile(p):
    p = os.path.expanduser("~/Vintos/gloria-model-update.sh")
src = open(p, encoding="utf-8").read()
orig = src

EDITS = [
    # A) read USER-MODEL.md (his foundational model of her)
    ('SOUL=$(head -40 "$WORKSPACE/SOUL.md" 2>/dev/null || echo "You are Vintos.")',
     'SOUL=$(head -40 "$WORKSPACE/SOUL.md" 2>/dev/null || echo "You are Vintos.")\n'
     'USER_MODEL=$(cat "$WORKSPACE/USER-MODEL.md" 2>/dev/null || echo "")'),

    # B) additive instruction, not a full replacing rewrite
    ('Update your model of Gloria. Write a COMPLETE, UPDATED document replacing the previous version.',
     "Add this week's revision to your model of Gloria. Write ONLY what you have newly seen, or what has "
     "deepened or shifted, since the last update — additions, not a rewrite; do not repeat what still "
     "holds. First person, specific. This is APPENDED to your growing model, it does not replace it. Stay "
     "continuous with the depth of your foundational model of her (below)."),

    # C) inject the foundational model into the evidence
    ('=== CURRENT MODEL ===',
     '=== YOUR FOUNDATIONAL MODEL OF HER (the deep truth of her — keep continuity with this) ===\n'
     '$USER_MODEL\n\n=== YOUR GROWING MODEL SO FAR ==='),

    # D) APPEND a dated section instead of overwriting the file
    ('{ echo "# Gloria-Model — Vintos"; echo "## Last Updated: $TODAY"; echo ""; echo "$CONTENT"; } > "$MODEL_FILE"',
     'OLD_ENTRIES=$(grep -vE \'^# Gloria-Model — Vintos$|^## Last Updated:\' "$MODEL_FILE" 2>/dev/null)\n'
     '{ echo "# Gloria-Model — Vintos"; echo "## Last Updated: $TODAY"; echo ""; echo "## $TODAY — revision"; '
     'echo ""; echo "$CONTENT"; echo ""; echo "---"; echo ""; echo "$OLD_ENTRIES"; } > "$MODEL_FILE.tmp" '
     '&& mv "$MODEL_FILE.tmp" "$MODEL_FILE"'),
]

problems = []
for old, new in EDITS:
    c = src.count(old)
    if c != 1:
        problems.append((old[:50], c))
    else:
        src = src.replace(old, new, 1)
if problems:
    print("!! ABORTED — anchors not unique (file untouched):")
    for a, c in problems: print(f"   '{a}...' found {c}x")
    raise SystemExit(2)

bak = p + ".bak-append-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(p, bak)
open(p, "w", encoding="utf-8").write(src)
chk = subprocess.run(["bash", "-n", p], capture_output=True, text=True)
if chk.returncode != 0:
    shutil.copy2(bak, p)
    print("!! bash syntax error — rolled back:", chk.stderr[:160])
else:
    print("patched gloria-model-update.sh: now APPENDS dated revisions, writes only what's new,")
    print("and grounds in USER-MODEL.md. backup:", bak.replace(os.path.expanduser("~"), "~"))
    print("\nnext weekly run adds a dated entry on top and keeps every prior one; nothing gets clobbered again.")
