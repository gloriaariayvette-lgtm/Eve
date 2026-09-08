#!/usr/bin/env python3
"""patch_ledger_truncate.py — Aegis. Match the journal's readable+truncated ledger render (150 chars/side)
instead of full json.dumps, freeing reasoning headroom. Backup + bash -n + hang-safe measure."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
t = open(P, encoding="utf-8", errors="ignore").read()
old = "print(json.dumps(e))"
new = "print('Gloria: ' + e.get('gloria','')[:150] + ' | Velaris: ' + e.get('velaris','')[:150])"
if new in t:
    print("already truncated")
elif t.count(old) == 1:
    t = t.replace(old, new, 1)
    bak = P + ".bak-ltrunc-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
    open(P, "w", encoding="utf-8").write(t)
    c = subprocess.run(["bash", "-n", P], capture_output=True, text=True)
    if c.returncode: shutil.copy2(bak, P); print("bash -n failed, reverted:", c.stderr[:100]); raise SystemExit(1)
    print("ledger entries -> readable + 150-char (matches journal)")
else:
    print(f"anchor x{t.count(old)} — abort"); raise SystemExit(1)

src = open(P, encoding="utf-8").read().replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
src = re.sub(r"INTRO_SEMANTIC=\$\(python3 << 'INTROSEMEOF'.*?INTROSEMEOF\n\)", 'INTRO_SEMANTIC=""', src, flags=re.S)
anc = "printf '%s' \"$FULL_PROMPT\" > /tmp/velaris_intro_prompt.txt"
src = src.replace(anc, anc + "\nexit 0", 1)
open("/tmp/pt.sh", "w", encoding="utf-8").write(src)
subprocess.run(["timeout", "90", "bash", "/tmp/pt.sh"], capture_output=True, text=True)
f = "/tmp/velaris_intro_prompt.txt"
n = os.path.getsize(f); sysn = os.path.getsize("/tmp/velaris_intro_system.txt")
tot = (n + sysn)//4
print(f"user {n:,}c (~{n//4:,}tok) + system {sysn:,}c = ~{tot:,}tok | reasoning room ~{32000-tot:,}tok")
