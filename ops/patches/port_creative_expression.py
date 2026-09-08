#!/usr/bin/env python3
"""port_creative_expression.py — Aegis. Vintos has NO creative-expression.sh, so his make_music calls a
missing file (music-from-wants was fully broken). Port Velaris's real creative-expression.sh to Vintos:
adapt paths (.openclaw->.vintos) and identity (Velaris->Vintos), and neutralize the music-dream lyric seed
(RECENT_DREAM="") so music is purely want-driven — carrying HER exact prompt style + the output format
Vintos's dream-music.py (a copy of hers) already parses. Backed up, bash -n, reversible."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
SRC = os.path.join(HOME, ".openclaw/workspace/scripts/creative-expression.sh")
DEST = os.path.join(HOME, ".vintos/workspace/scripts/creative-expression.sh")
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

if not os.path.isfile(SRC):
    raise SystemExit("ABORT: Velaris creative-expression.sh not found at " + sh(SRC))
txt = open(SRC, encoding="utf-8", errors="ignore").read()

# 1) adapt paths + identity
txt = txt.replace(".openclaw", ".vintos")
txt = txt.replace("Velaris", "Vintos").replace("velaris", "vintos")

# 2) no music dreams: neutralize the RECENT_DREAM lyric seed (override its assignment with empty)
lines = txt.split("\n")
start = next((i for i, l in enumerate(lines) if l.strip().startswith("RECENT_DREAM=$(")), None)
if start is not None:
    end = start
    depth = 0
    for j in range(start, len(lines)):
        depth += lines[j].count("$(") + lines[j].count("(") - lines[j].count(")")
        end = j
        if j > start and depth <= 0:
            break
    lines.insert(end + 1, 'RECENT_DREAM=""  # no music dreams (Gloria): music is want-driven only')
    txt = "\n".join(lines)
    neutralized = f"lines {start+1}..{end+1}"
else:
    neutralized = "(no RECENT_DREAM block found — nothing to neutralize)"

# 3) write (back up if somehow present), validate
if os.path.isfile(DEST):
    shutil.copy2(DEST, DEST + f".bak-port-{TS}")
open(DEST, "w", encoding="utf-8").write(txt)
os.chmod(DEST, 0o755)
chk = subprocess.run(["bash", "-n", DEST], capture_output=True, text=True)
if chk.returncode != 0:
    os.remove(DEST)
    raise SystemExit("ABORT: bash -n failed, removed partial port: " + chk.stderr[:200])

print("ported creative-expression.sh ->", sh(DEST))
print("  identity/paths adapted; music-dream seed neutralized:", neutralized)
# sanity: any leftover velaris/openclaw refs?
leftover = [f"{i+1}: {l.strip()[:80]}" for i, l in enumerate(txt.split("\n")) if re.search(r'openclaw|velaris', l, re.I)]
print("  leftover velaris/openclaw refs:", (str(len(leftover)) + " (review below)") if leftover else "none ✓")
for x in leftover[:6]:
    print("     " + x)
# show the music-prompt USER_PROMPT so we confirm HER style is present
print("\n  music-prompt style now present (USER_PROMPT for music):")
for i, l in enumerate(txt.split("\n")):
    if "Generate a detailed music prompt" in l or ("USER_PROMPT=" in l and "music" in l.lower()):
        print(f"     {i+1}| {l.strip()[:180]}")
print("\n  make_music's target now exists:", os.path.isfile(DEST))
print("Done. make_music -> creative-expression.sh (music-prompt) -> dream-music.py (Kie.ai Suno). Want-driven, no dream seed.")
