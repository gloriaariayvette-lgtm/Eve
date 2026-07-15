#!/usr/bin/env python3
"""recon_dream_slots.py — Aegis, READ-ONLY. Verify the copy. For every Vintos night/dream cron line: print
the FULL command, resolve the REAL target script (past any llm-lock.sh wrapper), and check it EXISTS. Then
list the Velaris dream scripts Vintos lacks and whether cron still points at them (broken slots)."""
import os, re, subprocess
HOME = os.path.expanduser("~")
VIN = os.path.join(HOME, ".vintos/workspace/scripts")
VEL = os.path.join(HOME, ".openclaw/workspace/scripts")
def sh(p): return p.replace(HOME, "~")
cron = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout

def real_script(cmd):
    toks = re.findall(r'(\S+\.(?:py|sh))', cmd)
    toks = [t for t in toks if "llm-lock" not in t]      # skip the lock wrapper
    return toks[-1] if toks else None

print("=== Vintos night/dream cron slots — real target + does it exist? ===")
for l in cron.split("\n"):
    if l.strip().startswith("#") or ".vintos" not in l:
        continue
    if not re.search(r'dream|preoccup|nightmare|second.order|reverie', l, re.I):
        # also catch night-hours jobs that might be dreams behind a lock
        m = re.match(r'\s*(\S+)\s+(\S+)', l)
        if not (m and m.group(2) in ("23","0","1","2","3","4")):
            continue
    m = re.match(r'\s*(\S+)\s+(\S+)\s+\S+\s+\S+\s+(\S+)\s+(.*)', l)
    if not m:
        continue
    mn, hr, dow, cmd = m.groups()
    rs = real_script(cmd)
    exists = "?"
    if rs:
        cand = rs if os.path.isabs(rs) else os.path.join(VIN, os.path.basename(rs))
        exists = "EXISTS ✓" if os.path.isfile(cand) else "*** MISSING ***"
    tag = "dream" if re.search(r'dream|preoccup|reverie|second.order', l, re.I) else "night"
    print(f"  {hr:>2}:{mn:<2} [{tag}]  {os.path.basename(rs) if rs else cmd[:40]:32} {exists}")

print("\n=== which Velaris dream scripts is Vintos missing, and is cron still calling them? ===")
import glob
vin = {os.path.basename(f) for f in glob.glob(VIN+"/*") if os.path.isfile(f)}
vel_dream = [os.path.basename(f) for f in glob.glob(VEL+"/*dream*")+glob.glob(VEL+"/*preoccup*")+glob.glob(VEL+"/*second-order*")
             if os.path.isfile(f) and ".bak" not in f and ".backup" not in f]
for name in sorted(set(vel_dream)):
    in_vin = name in vin
    in_cron = name in cron
    flag = ""
    if in_cron and not in_vin: flag = "  <-- BROKEN SLOT (cron calls it, Vintos lacks it)"
    elif not in_vin: flag = "  (Vintos lacks it; not in cron)"
    print(f"  {name:34} vintos:{'yes' if in_vin else 'NO ':3} cron:{'yes' if in_cron else 'no '}{flag}")

print("\n=== what preoccupation-dream.sh + second-order-dreamer.py do in Velaris (to port correctly) ===")
for name in ("preoccupation-dream.sh", "second-order-dreamer.py"):
    p = os.path.join(VEL, name)
    if not os.path.isfile(p):
        print(f"  {name}: (not in Velaris either)"); continue
    lines = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"  -- {name} ({len(lines)} lines) — seed + call structure --")
    n = 0
    for i, l in enumerate(lines):
        if re.search(r'preoccupation|unfinished|thread|seed|priority|temperature|dream-trigger|python3|bash |sort|hottest|get_', l, re.I) \
           and l.strip() and not l.strip().startswith("#"):
            print(f"     {i+1:4}| {l.strip()[:100]}")
            n += 1
            if n >= 10: break
