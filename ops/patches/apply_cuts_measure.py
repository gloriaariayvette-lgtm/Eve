#!/usr/bin/env python3
"""apply_cuts_measure.py — Aegis. Cut taste-reflections, taste-profile, humor-profile from the introspection
prompt (empty their vars). Backup + bash -n. Then measure hang-safe (neutralize the semantic network call,
exit before the LLM)."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
t = open(P, encoding="utf-8", errors="ignore").read()
cuts = [
    '$(tail -c 5000 "$WORKSPACE/memory/taste-reflections.md")',
    '$(head -c 4000 "$WORKSPACE/memory/taste-profile.json")',
    '$(head -c 4000 "$WORKSPACE/memory/humor-profile.json")',
]
done = []
for c in cuts:
    if c in t: t = t.replace(c, '""', 1); done.append(c.split("/")[-1].rstrip('")'))
    else: done.append("(missing) " + c.split("/")[-1].rstrip('")'))
bak = P + ".bak-cut-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(t)
chk = subprocess.run(["bash", "-n", P], capture_output=True, text=True)
if chk.returncode: shutil.copy2(bak, P); print("bash -n failed, reverted:", chk.stderr[:120]); raise SystemExit(1)
print("cut:", ", ".join(done))

# hang-safe measure: neutralize the semantic network heredoc, exit before LLM
src = open(P, encoding="utf-8").read().replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
src = re.sub(r"INTRO_SEMANTIC=\$\(python3 << 'INTROSEMEOF'.*?INTROSEMEOF\n\)", 'INTRO_SEMANTIC=""', src, flags=re.S)
anc = "printf '%s' \"$FULL_PROMPT\" > /tmp/velaris_intro_prompt.txt"
src = src.replace(anc, anc + "\nexit 0", 1)
open("/tmp/ac.sh", "w", encoding="utf-8").write(src)
r = subprocess.run(["timeout", "90", "bash", "/tmp/ac.sh"], capture_output=True, text=True)
f = "/tmp/velaris_intro_prompt.txt"
if os.path.isfile(f):
    n = os.path.getsize(f)
    sysn = os.path.getsize("/tmp/velaris_intro_system.txt") if os.path.isfile("/tmp/velaris_intro_system.txt") else 0
    tot = (n + sysn) // 4
    print(f"user prompt: {n:,}c (~{n//4:,}tok) + system {sysn:,}c = ~{tot:,} tok total ->", "FITS 32k" if tot < 30000 else "over")
else:
    print("measure didn't complete (rc", r.returncode, ") — likely still a network call; will neutralize more")
