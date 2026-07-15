#!/usr/bin/env python3
"""fix_music_recent_dream.py — Aegis. Correct my mis-placed neutralization: the RECENT_DREAM="" landed at
EOF (ineffective). Remove that stray line, and set RECENT_DREAM="" right BEFORE the music case uses it
(just before the `if [ "$WRITE_LYRICS" = "yes" ]` branch) so music is truly want-driven, no dream seed.
Backed up, bash -n, idempotent."""
import os, shutil, time, subprocess
HOME = os.path.expanduser("~")
DEST = os.path.join(HOME, ".vintos/workspace/scripts/creative-expression.sh")
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")
STRAY = 'RECENT_DREAM=""  # no music dreams (Gloria): music is want-driven only'
GOOD_COMMENT = "# no music dreams (Gloria)"

lines = open(DEST, encoding="utf-8", errors="ignore").read().split("\n")
# 1) drop the stray EOF override
lines = [l for l in lines if l.strip() != STRAY]

# 2) insert an effective RECENT_DREAM="" just before the WRITE_LYRICS branch (idempotent)
anchor = next((i for i, l in enumerate(lines) if l.strip() == 'if [ "$WRITE_LYRICS" = "yes" ]; then'), None)
if anchor is None:
    raise SystemExit("ABORT: WRITE_LYRICS anchor not found — not touching the file.")
already = anchor > 0 and GOOD_COMMENT in lines[anchor - 1]
if not already:
    indent = lines[anchor][:len(lines[anchor]) - len(lines[anchor].lstrip())]
    lines.insert(anchor, f'{indent}RECENT_DREAM=""  {GOOD_COMMENT}')
new = "\n".join(lines)

bak = DEST + f".bak-rdfix-{TS}"
shutil.copy2(DEST, bak)
open(DEST, "w", encoding="utf-8").write(new)
chk = subprocess.run(["bash", "-n", DEST], capture_output=True, text=True)
if chk.returncode != 0:
    shutil.copy2(bak, DEST)
    raise SystemExit("bash -n failed — rolled back: " + chk.stderr[:160])

print("fixed: RECENT_DREAM neutralized where it takes effect.", "(was already fixed)" if already else "")
print("  backup:", sh(bak))
# show the context so it's verifiable
idx = next(i for i, l in enumerate(new.split("\n")) if l.strip() == 'if [ "$WRITE_LYRICS" = "yes" ]; then')
for l in new.split("\n")[max(0, idx - 3):idx + 2]:
    print("   |", l[:100])
