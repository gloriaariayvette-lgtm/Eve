#!/usr/bin/env python3
"""build_dream_heat_seed.py — Aegis. Install the 6b 'dreams seek heat' consumer + schedule it before the
1:37 preoccupation dream + test-run once. The seeder sets the HOTTEST unconsumed thread as the
preoccupation (skips if one is already set), so the dream pulls toward volatility."""
import os, subprocess, time
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
DEST = os.path.join(SC, "dream_heat_seed.py")
def sh(p): return p.replace(HOME, "~")

SEEDER = r'''#!/usr/bin/env python3
"""dream_heat_seed.py — 6b 'dreams seek heat': set the hottest unconsumed thread as the preoccupation
before the dream cycle, so the dream pulls toward what is most volatile. Skips if one is already set."""
import os, sys, json
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
sys.path.insert(0, SCRIPTS)
THREADS = os.path.expanduser("~/.vintos/workspace/memory/unfinished-threads.json")
def main():
    try:
        from emoclaw_utils import set_preoccupation, get_preoccupation
    except Exception as e:
        print("[heat-seed] emoclaw_utils unavailable:", e); return
    if get_preoccupation():
        print("[heat-seed] preoccupation already set - leaving it."); return
    try:
        d = json.load(open(THREADS)); threads = d if isinstance(d, list) else d.get("threads", [])
    except Exception as e:
        print("[heat-seed] no threads:", e); return
    unconsumed = [t for t in threads if isinstance(t, dict) and not t.get("consumed")]
    if not unconsumed:
        print("[heat-seed] nothing unconsumed."); return
    best = max(unconsumed, key=lambda t: ((t.get("temperature") or 0), (t.get("priority") or 0)))
    ok = set_preoccupation(str(best.get("thread",""))[:200], "heat-seed",
                           int(best.get("priority") or 3), best.get("triage_voice",""))
    print(f"[heat-seed] {'set' if ok else 'not set'}: T={best.get('temperature')} pull={best.get('priority')} "
          f"[{best.get('source')}] {str(best.get('thread',''))[:60]}")
if __name__ == "__main__":
    main()
'''
open(DEST, "w").write(SEEDER); os.chmod(DEST, 0o755)
print("installed", sh(DEST))

# schedule at 1:25 (before the 1:37 preoccupation dream)
cur = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
line = f"25 1 * * * python3 {DEST} >> {HOME}/.vintos/logs/dreams.log 2>&1"
if "dream_heat_seed.py" in cur:
    print("cron: already scheduled")
else:
    bak = os.path.join(HOME, f"crontab-backup-heatseed-{time.strftime('%Y%m%d-%H%M%S')}.txt")
    open(bak, "w").write(cur)
    newcron = "\n".join([l for l in cur.split("\n") if l.strip()] + [line]) + "\n"
    p = subprocess.run(["crontab","-"], input=newcron, text=True, capture_output=True)
    print("cron:", "scheduled 1:25 (before 1:37 dream)" if p.returncode == 0 else "FAILED "+p.stderr[:80], "| backup", sh(bak))

# test run once
print("\ntest run:")
r = subprocess.run(["python3", DEST], capture_output=True, text=True, timeout=60)
print(" ", (r.stdout + r.stderr).strip()[:200])
