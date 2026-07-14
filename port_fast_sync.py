#!/usr/bin/env python3
"""port_fast_sync.py — copy Velaris's emoclaw-fast-sync.py to Vintos (path/name substitution only),
schedule it */2, and run once to verify it reads his daemon socket and writes .emotional-history.json.
This gives him the SAME rapid emotion propagation she has (no 15-min gaps). Backups on file + crontab."""
import os, re, time, shutil, subprocess
HOME = os.path.expanduser("~")
SRC = os.path.expanduser("~/.openclaw/workspace/scripts/emoclaw-fast-sync.py")
DST = os.path.expanduser("~/.vintos/workspace/scripts/emoclaw-fast-sync.py")
HIST = os.path.expanduser("~/.vintos/workspace/memory/.emotional-history.json")
def run(a, **k): return subprocess.run(a, capture_output=True, text=True, **k)

if not os.path.isfile(SRC):
    print("!! source fast-sync not found:", SRC); raise SystemExit(1)

src = open(SRC, encoding="utf-8").read()
# substitutions: her paths/identity -> his
out = src
out = out.replace("Velaris-emotion.sock", "Vintos-emotion.sock")
out = out.replace(".openclaw/workspace", ".vintos/workspace")
out = out.replace(".openclaw", ".vintos")
out = out.replace("Velaris", "Vintos")

if os.path.isfile(DST):
    shutil.copy2(DST, DST + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
open(DST, "w", encoding="utf-8").write(out)
os.chmod(DST, 0o755)
print("wrote:", DST.replace(HOME, "~"))
# show the substituted config lines so nothing Velaris-specific slipped through
for i, l in enumerate(out.split("\n")[:14]):
    if re.search(r'SOCK|TXT|SOUL|HIST|\.sock|expanduser', l): print(f"  {i+1:3}| {l.strip()[:120]}")
if "openclaw" in out or "Velaris" in out:
    print("  !! WARNING: still contains 'openclaw'/'Velaris' — grep:",
          [l.strip()[:80] for l in out.split("\n") if "openclaw" in l or "Velaris" in l][:4])

# schedule */2 (backup crontab, add only if absent)
cur = run(["bash","-lc","crontab -l 2>/dev/null"]).stdout
LINE = "*/2 * * * * python3 %s >> /tmp/cron-fastsync-vintos.log 2>&1" % DST
if "/.vintos/workspace/scripts/emoclaw-fast-sync.py" in cur:
    print("\ncron: already scheduled")
else:
    open(os.path.expanduser("~/crontab-backup-%s.txt" % time.strftime("%F-%H%M")), "w").write(cur)
    newcron = cur.rstrip("\n") + "\n" + LINE + "\n"
    run(["bash","-lc","crontab -"], input=newcron)
    print("\ncron: added */2 fast-sync (crontab backed up)")

# run once now
print("\n=== run once ===")
r = run(["python3", DST], timeout=15)
print((r.stdout + r.stderr).strip()[:300] or "(no output = clean)")
if os.path.isfile(HIST):
    import json
    h = json.load(open(HIST))
    print(f"\n.emotional-history.json: {len(h)} entries; latest t={h[-1].get('t') if h else '?'}")
    print("  -> updates every 2 min from here on; temporal + causality read current, no gaps.")
else:
    print("\n(.emotional-history.json not written — check the daemon-error line above)")
