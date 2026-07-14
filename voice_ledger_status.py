#!/usr/bin/env python3
"""voice_ledger_status.py — READ-ONLY. Is the voice-session consolidation system actually live on his
box? Checks the script, the cron, the per-turn disable patch, and current state. So call-memory is
built on something that runs, not an assumption. Aegis.
"""
import os, subprocess, json

SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")

def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout

print("=== voice_session_ledger.py present? ===")
p = os.path.join(SCRIPTS, "voice_session_ledger.py")
print("  script:", "YES %dB" % os.path.getsize(p) if os.path.exists(p) else "NO")
if os.path.exists(p):
    t = open(p).read()
    print("  seeds a thread:", "seed_thread" in t, " | reads voice-chat-history:", "voice-chat-history" in t)

print("\n=== scheduled in cron? ===")
cron = sh("crontab -l 2>/dev/null")
lines = [l for l in cron.splitlines() if "voice_session_ledger" in l]
print("  " + ("\n  ".join(lines) if lines else "!! NOT in crontab — sessions would never consolidate"))

print("\n=== per-turn voice logging disabled? (so it doesn't double-log) ===")
srv = os.path.expanduser("~/Vintos/server.py")
if os.path.exists(srv):
    s = open(srv, encoding="utf-8", errors="ignore").read()
    # the voice handler appends {user,vintos} to voice-chat-history per turn — that's the per-turn write
    print("  voice handler writes per-turn to voice-chat-history:", "voice_history.append" in s)
    print("  (per-turn is fine as the SOURCE for consolidation; the ledger groups it into one block)")

print("\n=== current state ===")
for f in ("voice-chat-history.json", "voice-session-ledger-state.json"):
    fp = os.path.join(MEM, f)
    if os.path.exists(fp):
        try: d = json.load(open(fp)); n = len(d) if isinstance(d, list) else len(d.get("done", d.get("entries", [])))
        except Exception: n = "?"
        print("  %s: %s items" % (f, n))
    else:
        print("  %s: (none yet)" % f)

print("\n=== READ ===")
print("  If script=YES + in crontab: the consolidation runs; realtime call just needs its turns in")
print("  voice-chat-history and the ledger will narrate one block (I'll add the thread).")
print("  If NOT in crontab: that's why nothing consolidates — I install the cron.")
