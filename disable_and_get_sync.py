#!/usr/bin/env python3
"""disable_and_get_sync.py —
 A) DISABLE (both): neuter kiss/anti-kiss/possessiveness/anger expression scripts (Velaris has them;
    backup + early-exit guard, reversible). Then check if Vintos carries the behavior in shared code.
 B) Dump Velaris's emoclaw-fast-sync.py (capped) so I can port the rapid pipeline to Vintos next.
Aegis."""
import os, re, glob, subprocess, time, shutil
HOME = os.path.expanduser("~")
VS = os.path.expanduser("~/.openclaw/workspace/scripts")
TS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout

TARGETS = ["anger-expression.sh", "anti-kiss.sh", "dream-kiss-check.sh",
           "kiss-haptic.sh", "kiss-threshold.sh", "possessiveness-detector.sh"]
GUARD = "# --- DISABLED per Gloria: kiss/anti-kiss/possessiveness/anger expression off ---\nexit 0\n"

print("=== A) disabling expression scripts (Velaris) ===")
for name in TARGETS:
    p = os.path.join(VS, name)
    if not os.path.isfile(p):
        print(f"  {name}: (not found)"); continue
    src = open(p, encoding="utf-8", errors="ignore").read()
    if "DISABLED per Gloria" in src:
        print(f"  {name}: already disabled"); continue
    shutil.copy2(p, p + ".bak-disable-" + time.strftime("%Y%m%d-%H%M%S"))
    lines = src.split("\n")
    if lines and lines[0].startswith("#!"):
        new = lines[0] + "\n" + GUARD + "\n".join(lines[1:])
    else:
        new = GUARD + src
    open(p, "w", encoding="utf-8").write(new)
    print(f"  {name}: DISABLED (backup made)")

print("\n=== A) does VINTOS carry kiss/possess/anger behavior in shared code? ===")
hits = run(["bash","-lc",
    f"grep -rlnE 'kiss|possess|anger|jealous' {TS} {os.path.join(VIN)} --include=*.py --include=*.sh 2>/dev/null "
    f"| grep -viE '\\.bak|\\.pyc' | head"]).strip().split("\n")
print("  files mentioning kiss/possess/anger:", [os.path.basename(h) for h in hits if h] or "(none)")
# is it wired into his emoclaw daemon / utils?
for f in ("emoclaw_utils.py",):
    p = os.path.join(TS, f)
    if os.path.isfile(p):
        n = 0
        for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
            if re.search(r'kiss|possess|anger|jealous', l, re.I) and l.strip():
                print(f"    emoclaw_utils {i+1}| {l.strip()[:120]}"); n += 1
                if n >= 6: break
        if n == 0: print("    emoclaw_utils.py: no kiss/possess/anger refs")

print("\n=== B) Velaris emoclaw-fast-sync.py (port source, capped 48 lines) ===")
fs = os.path.join(VS, "emoclaw-fast-sync.py")
if os.path.isfile(fs):
    ls = open(fs, encoding="utf-8", errors="ignore").read().split("\n")
    for i in range(min(48, len(ls))):
        print(f"  {i+1:3}| {ls[i][:150]}")
    if len(ls) > 48: print(f"  ...({len(ls)-48} more lines)")
