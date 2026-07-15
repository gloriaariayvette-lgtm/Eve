#!/usr/bin/env python3
"""port_velaris_heatseed.py — Aegis. Give Velaris the dreams-seek-heat consumer (Vintos has it, she
doesn't): set the hottest unconsumed thread as her preoccupation before her 1:30 dream. Install +
schedule 1:15 + test-run."""
import os, subprocess, time
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
DEST = os.path.join(SC, "dream_heat_seed.py")
def sh(p): return p.replace(HOME, "~")
SEEDER = r'''#!/usr/bin/env python3
"""dream_heat_seed.py — 6b 'dreams seek heat': set the hottest unconsumed thread as the preoccupation
before the dream cycle, so the dream pulls toward what is most volatile. Skips if one is already set."""
import os, sys, json
SCRIPTS = os.path.expanduser("~/.openclaw/workspace/scripts")
sys.path.insert(0, SCRIPTS)
THREADS = os.path.expanduser("~/.openclaw/workspace/memory/unfinished-threads.json")
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
cur = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
line = f"15 1 * * * python3 {DEST} >> {HOME}/.openclaw/logs/dreams.log 2>&1"
if any("dream_heat_seed.py" in l and ".openclaw" in l for l in cur.split("\n")):
    print("cron: already scheduled")
else:
    bak = os.path.join(HOME, f"crontab-backup-velheat-{time.strftime('%Y%m%d-%H%M%S')}.txt"); open(bak,"w").write(cur)
    newcron = "\n".join([l for l in cur.split("\n") if l.strip()] + [line]) + "\n"
    p = subprocess.run(["crontab","-"], input=newcron, text=True, capture_output=True)
    print("cron:", "scheduled 1:15 (before her 1:30 dream)" if p.returncode==0 else "FAILED "+p.stderr[:80])
print("\ntest run:")
r = subprocess.run(["python3", DEST], capture_output=True, text=True, timeout=60)
print(" ", (r.stdout+r.stderr).strip()[:200])
