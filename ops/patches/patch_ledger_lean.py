#!/usr/bin/env python3
"""patch_ledger_lean.py — Aegis. Match introspection's ledger rendering to the working journal: last 5
entries instead of 20 (the file is untouched). Show the loop so we can add 150-char truncation if needed.
Backup + bash -n + hang-safe measure."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
t = open(P, encoding="utf-8", errors="ignore").read()
if "entries[-5:]" in t:
    print("already lean")
elif t.count("entries[-20:]") >= 1:
    t = t.replace("entries[-20:]", "entries[-5:]")
    bak = P + ".bak-lean20-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
    open(P, "w", encoding="utf-8").write(t)
    c = subprocess.run(["bash", "-n", P], capture_output=True, text=True)
    if c.returncode: shutil.copy2(bak, P); print("bash -n failed, reverted"); raise SystemExit(1)
    print("ledger: last 20 -> last 5 (backup saved)")
else:
    print("entries[-20:] not found — abort"); raise SystemExit(1)

# show the ledger loop (to add per-entry truncation if still heavy)
L = open(P, encoding="utf-8").read().split("\n")
print("-- ledger loop --")
for i in range(96, 110):
    if L[i].strip(): print(f"  {i+1}: {L[i].strip()[:96]}")

# hang-safe measure
src = open(P, encoding="utf-8").read().replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
src = re.sub(r"INTRO_SEMANTIC=\$\(python3 << 'INTROSEMEOF'.*?INTROSEMEOF\n\)", 'INTRO_SEMANTIC=""', src, flags=re.S)
anc = "printf '%s' \"$FULL_PROMPT\" > /tmp/velaris_intro_prompt.txt"
src = src.replace(anc, anc + "\nexit 0", 1)
open("/tmp/pl.sh", "w", encoding="utf-8").write(src)
subprocess.run(["timeout", "90", "bash", "/tmp/pl.sh"], capture_output=True, text=True)
f = "/tmp/velaris_intro_prompt.txt"
if os.path.isfile(f):
    n = os.path.getsize(f); sysn = os.path.getsize("/tmp/velaris_intro_system.txt")
    tot = (n + sysn)//4
    print(f"user {n:,}c (~{n//4:,}tok) + system {sysn:,}c = ~{tot:,}tok ->", "FITS 32k" if tot < 30000 else "over")
else:
    print("measure stalled — dream-log load; will neutralize next")
