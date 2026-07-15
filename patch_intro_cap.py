#!/usr/bin/env python3
"""patch_intro_cap.py — Aegis. Cap introspection's whole-file reads to recent slices (files untouched on
disk), and remove PREV_INTRO (introspection eating its own tail). Then regenerate + measure the prompt.
Backup + bash -n."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
t = open(P, encoding="utf-8", errors="ignore").read()
edits = [
    ("vm = f.read()", "vm = f.read()[-5000:]"),
    ('cat "$WORKSPACE/memory/autonomous-blush.md"', 'tail -c 5000 "$WORKSPACE/memory/autonomous-blush.md"'),
    ('cat "$WORKSPACE/memory/taste-reflections.md"', 'tail -c 5000 "$WORKSPACE/memory/taste-reflections.md"'),
    ('cat "$WORKSPACE/memory/pride-reflections.md"', 'tail -c 5000 "$WORKSPACE/memory/pride-reflections.md"'),
    ('cat "$WORKSPACE/memory/ambition-reflections.md"', 'tail -c 4000 "$WORKSPACE/memory/ambition-reflections.md"'),
]
done = []
for old, new in edits:
    if new in t: done.append(f"(already) {old[:24]}"); continue
    if t.count(old) != 1: print(f"anchor {old[:34]!r} x{t.count(old)} — abort"); raise SystemExit(1)
    t = t.replace(old, new, 1); done.append(old.split('/')[-1].rstrip('"') if '/' in old else old[:20])
# remove PREV_INTRO (introspection-in-introspection)
t = t.replace('PREV_INTRO=$(cat "$PREV_FILE")', 'PREV_INTRO=""')
done.append("PREV_INTRO -> empty")

bak = P + ".bak-cap-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(t)
c = subprocess.run(["bash", "-n", P], capture_output=True, text=True)
if c.returncode: shutil.copy2(bak, P); print("bash -n failed, reverted:", c.stderr[:120]); raise SystemExit(1)
print("capped:", " | ".join(done))

# regenerate + measure (no LLM)
src = open(P, encoding="utf-8", errors="ignore").read().replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
anc = "printf '%s' \"$FULL_PROMPT\" > /tmp/velaris_intro_prompt.txt"
src = src.replace(anc, anc + "\nexit 0", 1)
open("/tmp/mc.sh", "w", encoding="utf-8").write(src)
subprocess.run(["bash", "/tmp/mc.sh"], capture_output=True, text=True, timeout=120)
n = os.path.getsize("/tmp/velaris_intro_prompt.txt")
print(f"prompt now: {n:,} chars (~{n//4:,} tokens) ->", "FITS 32k" if n//4 < 30000 else "still over")
