#!/usr/bin/env python3
"""fix_velaris_premonition_cron.py — Aegis. The port's cron check was too loose (matched Vintos's line +
any .openclaw line). Add Velaris's premonition cron only if no single line has BOTH her path + the script.
Also fix the cosmetic 'his'->'her' in her installed dreamer (she's she/her)."""
import os, subprocess, time
HOME = os.path.expanduser("~")
DEST = os.path.join(HOME, ".openclaw/workspace/scripts/premonition-dreamer.py")
LOGS = os.path.join(HOME, ".openclaw/logs")
LOCK = os.path.join(HOME, "llm-lock.sh")
def sh(p): return p.replace(HOME, "~")

cur = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
have = any(("premonition-dreamer.py" in l and ".openclaw" in l and not l.strip().startswith("#")) for l in cur.split("\n"))
if have:
    print("cron: her premonition line already present.")
else:
    wrap = f"bash {LOCK} " if os.path.isfile(LOCK) else ""
    line = f"30 22 * * * {wrap}python3 {DEST} >> {LOGS}/premonition.log 2>&1"
    bak = os.path.join(HOME, f"crontab-backup-velprem-{time.strftime('%Y%m%d-%H%M%S')}.txt")
    open(bak, "w").write(cur)
    newcron = "\n".join([l for l in cur.split("\n") if l.strip()] + [line]) + "\n"
    p = subprocess.run(["crontab","-"], input=newcron, text=True, capture_output=True)
    print("cron:", "ADDED 22:30 (before her 23:30 dream), lock-wrapped" if p.returncode==0 else "FAILED "+p.stderr[:80], "| backup", sh(bak))

# cosmetic: her pronoun in the installed dreamer
if os.path.isfile(DEST):
    t = open(DEST, encoding="utf-8", errors="ignore").read()
    t2 = t.replace("his dream cycle", "her dream cycle").replace("his NORMAL dream", "her NORMAL dream").replace("his own dream", "her own dream")
    if t2 != t:
        open(DEST, "w", encoding="utf-8").write(t2)
        print("pronoun: fixed 'his'->'her' in her dreamer's log/docstring.")
    else:
        print("pronoun: nothing to change.")
