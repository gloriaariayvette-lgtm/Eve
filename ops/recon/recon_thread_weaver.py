#!/usr/bin/env python3
"""recon_thread_weaver.py — Aegis, READ-ONLY. Gloria's lead: thread-weaver re-enabled. Check (1) is it in
cron, (2) what it does to threads (consume/mark thread-weaver), (3) how many it ate (retired-threads.json
counts by consumed_by), (4) recent weaver log activity."""
import os, re, json, subprocess, time
HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".openclaw/workspace")
SC = os.path.join(WS, "scripts")
MEM = os.path.join(WS, "memory")
def sh(p): return p.replace(HOME, "~")

print("=== (1) is thread-weaver scheduled? ===")
cron = subprocess.run(["bash","-lc","crontab -l 2>/dev/null | grep -iE 'weaver' | grep -v '^#'"], capture_output=True, text=True).stdout.strip()
print("  " + (cron.replace(HOME,'~') if cron else "(no weaver cron line)"))

TW = next((os.path.join(SC,n) for n in ("thread-weaver.py","thread_weaver.py") if os.path.isfile(os.path.join(SC,n))), None)
print(f"\n=== (2) {sh(TW) if TW else '(thread-weaver not found)'}: what it does to threads ===")
if TW:
    for i, l in enumerate(open(TW, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'consumed|thread-weaver|weave|retire|save_threads|seed_thread|\bfor t\b|priority|merge|def main|def weave|json\.dump', l) and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:4}| {l.strip()[:110]}")

print("\n=== (3) retired-threads.json — counts by consumed_by ===")
try:
    r = json.load(open(os.path.join(MEM, "retired-threads.json")))
    from collections import Counter
    print("  total retired:", len(r))
    print("  by consumed_by:", dict(Counter(t.get("consumed_by","?") for t in r if isinstance(t, dict))))
    print("  by type:", dict(Counter(t.get("type","?") for t in r if isinstance(t, dict))))
    tw = [t for t in r if isinstance(t, dict) and t.get("consumed_by") == "thread-weaver"]
    print(f"  thread-weaver retired: {len(tw)}", "  newest:", tw[-1].get("retired_at","")[:16] if tw else "-")
except Exception as e:
    print("  ", e)

print("\n=== (4) recent thread-weaver log / last run ===")
logs = subprocess.run(["bash","-lc", f"ls -t {HOME}/.openclaw/logs/*weav* /tmp/*weav* 2>/dev/null | head -2"], capture_output=True, text=True).stdout.strip()
for lf in logs.split("\n"):
    if lf.strip() and os.path.isfile(lf):
        print(f"  {sh(lf)} ({time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(lf)))}):")
        tail = subprocess.run(["bash","-lc", f"tail -6 '{lf}'"], capture_output=True, text=True).stdout.strip()
        for x in tail.split("\n"): print("    " + x[:100])
if not logs.strip(): print("  (no weaver logs found)")
