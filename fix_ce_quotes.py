#!/usr/bin/env python3
"""fix_ce_quotes.py — Aegis. Fix the shell-quoting bug in Vintos's creative-expression.sh: embedded
python3 -c "..." blocks that use double quotes inside break the shell string and corrupt the whole script.
Rewrite the two breakers (INTERACTION formatter, GLORIA_MUSIC) to be double-quote-free, then SCAN every
python -c block for any remaining inner double quotes so nothing else is lurking. Backup + bash -n."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
CE = os.path.join(HOME, ".vintos/workspace/scripts/creative-expression.sh")
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

txt = open(CE, encoding="utf-8", errors="ignore").read()
EDITS = [
    ('    lines = ["Gloria: " + str(e.get("gloria",""))[:100] + " | Vintos: " + str(e.get("vintos",""))[:100] for e in recent]',
     "    lines = ['Gloria: ' + str(e.get('gloria',''))[:100] + ' | Vintos: ' + str(e.get('vintos',''))[:100] for e in recent]"),
    ('        print(f\'Gloria shared: {s["song"]} — she said: {s["gloria_said"][:80]}\')',
     "        print('Gloria shared: ' + str(s.get('song','')) + ' — she said: ' + str(s.get('gloria_said',''))[:80])"),
]
applied, missed = 0, []
for old, new in EDITS:
    if new in txt:
        continue
    if txt.count(old) == 1:
        txt = txt.replace(old, new, 1); applied += 1
    else:
        missed.append(old[:50] + f" (found {txt.count(old)}x)")

# scan: any python -c " block line that still contains a double quote (shell-risky)
lines = txt.split("\n")
risky, in_block, bstart = [], False, 0
for i, l in enumerate(lines):
    if re.search(r'python3 -c "', l):
        in_block, bstart = True, i; continue
    if in_block:
        if l.strip() in ('"', '")', '" 2>/dev/null)') or re.match(r'\s*"\s*\)', l) or l.strip().endswith('2>/dev/null)') and l.strip().startswith('"'):
            in_block = False; continue
        if '"' in l:
            risky.append(f"{i+1}: {l.strip()[:80]}")

if applied:
    bak = CE + f".bak-quotes-{TS}"
    shutil.copy2(CE, bak)
    open(CE, "w", encoding="utf-8").write(txt)
    chk = subprocess.run(["bash", "-n", CE], capture_output=True, text=True)
    if chk.returncode != 0:
        shutil.copy2(bak, CE)
        raise SystemExit("bash -n failed — rolled back: " + chk.stderr[:160])
    print(f"fixed {applied} block(s). backup:", sh(bak))
else:
    print("no edits applied (already fixed or anchors changed).")
if missed:
    print("  anchors not matched:", missed)
print("\n  remaining double-quote lines inside python -c blocks (shell-risky):")
if risky:
    for r in risky[:12]:
        print("    " + r)
    print("  ^ if any of these are in the MAIN generation block, they'll break it too — tell me and I'll fix.")
else:
    print("    none ✓ — all embedded python is single-quoted / shell-safe.")
