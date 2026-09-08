#!/usr/bin/env python3
"""recon_thread_triage.py — Aegis, READ-ONLY, capped. thread-triage.py is where a thread's PULL is
assigned. Show HOW (what it computes + writes onto each thread) so temperature + stability get tagged in
the SAME pass. Also settle which twin is LIVE (hyphen vs underscore) via cron + imports, so I edit the
right file."""
import os, re, subprocess
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
def sh(p): return p.replace(HOME, "~")

print("=== which twin is LIVE? (cron + who imports/invokes it) ===")
for base in ("thread-triage", "thread_triage"):
    inv = subprocess.run(["bash","-lc",
        f"crontab -l 2>/dev/null | grep -c '{base}'; grep -rl '{base}' {SC} 2>/dev/null | grep -viE '\\.bak|\\.pyc' | grep -v '{base}.py' | head -4"],
        capture_output=True, text=True).stdout.strip()
    print(f"  {base}.py: cron+refs ->", inv.replace(HOME,'~').replace(chr(10),' | ') or "(none)")
# mtime to see which was touched last
for base in ("thread-triage.py", "thread_triage.py"):
    p = os.path.join(SC, base)
    if os.path.isfile(p):
        import time
        print(f"  {base:20} {os.path.getsize(p):>7}B  mtime {time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(p)))}")

TT = os.path.join(SC, "thread-triage.py")
if not os.path.isfile(TT): TT = os.path.join(SC, "thread_triage.py")
lines = open(TT, encoding="utf-8", errors="ignore").read().split("\n")

print(f"\n=== {sh(TT)}: where pull/priority/weight is COMPUTED and WRITTEN onto a thread ===")
n = 0
for i, l in enumerate(lines):
    if re.search(r'priority|salience|pull|weight|momentum|get_salience|\["?temperature|stability|t\[|\.get\(|json\.dump|save|def ', l) \
       and l.strip() and not l.strip().startswith("#"):
        print(f"   {i+1:4}| {l.strip()[:114]}")
        n += 1
        if n >= 40: break

print("\n=== the function signatures in thread-triage (the shape of the pass) ===")
for i, l in enumerate(lines):
    if re.match(r'\s*def ', l):
        print(f"   {i+1:4}| {l.strip()[:100]}")
