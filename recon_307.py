#!/usr/bin/env python3
"""recon_307.py — Aegis, READ-ONLY. Evidence only, no conclusions. The 1:37 dream fires, the 3:07 does
not. Show: (1) the raw night/dream crontab lines VERBATIM (no parsing), (2) where dream scripts actually
live (skills/dreaming/scripts), (3) the dream logs — tail + errors/tracebacks — especially anything near
03:. Let the logs say why 3:07 fails."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".vintos/workspace")
LOGS = os.path.join(HOME, ".vintos/logs")
def sh(p): return p.replace(HOME, "~")

print("=== (1) raw crontab — night/dream lines VERBATIM ===")
cron = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
for l in cron.split("\n"):
    if l.strip().startswith("#") or not l.strip():
        continue
    m = re.match(r'\s*(\S+)\s+(\S+)', l)
    hour = m.group(2) if m else ""
    if re.search(r'dream|preoccup|reverie|second.order|nightmare', l, re.I) or any(h in hour.split(",") for h in ("23","0","1","2","3","4")):
        print("  " + l.strip()[:140])

print("\n=== (2) where dream scripts actually live ===")
for d in (os.path.join(WS, "skills/dreaming/scripts"), os.path.join(WS, "scripts")):
    if os.path.isdir(d):
        fs = sorted(os.path.basename(f) for f in glob.glob(d+"/*dream*")+glob.glob(d+"/*preoccup*")+glob.glob(d+"/*second-order*"))
        print(f"  {sh(d)}:\n    {fs}")

print("\n=== (3) dream logs — tail + errors ===")
logfiles = sorted(glob.glob(LOGS+"/*dream*") + glob.glob(LOGS+"/dreams.log") + glob.glob(LOGS+"/preoccup*"))
if not logfiles:
    print("  (no dream logs found in", sh(LOGS), "— listing all logs:)")
    print("   ", sorted(os.path.basename(f) for f in glob.glob(LOGS+"/*"))[:30])
for lf in sorted(set(logfiles))[:6]:
    try:
        lines = open(lf, encoding="utf-8", errors="ignore").read().split("\n")
    except Exception as e:
        print(f"  {sh(lf)}: {e}"); continue
    errs = [f"{i+1}: {l.strip()[:110]}" for i, l in enumerate(lines)
            if re.search(r'error|traceback|no such file|not found|exception|failed|cannot|missing|command not found', l, re.I)]
    print(f"  -- {sh(lf)} ({len(lines)} lines) --")
    print("     last 6:")
    for l in [x for x in lines if x.strip()][-6:]:
        print("       " + l[:110])
    if errs:
        print(f"     {len(errs)} error line(s), last 6:")
        for e in errs[-6:]:
            print("       " + e)

print("\n=== the 3:07 script: what runs at 3:07, does it exist, any lock/log of its own ===")
for l in cron.split("\n"):
    m = re.match(r'\s*(\S+)\s+(\S+)\s+\S+\s+\S+\s+\S+\s+(.*)', l)
    if m and m.group(1) == "7" and m.group(2) == "3":
        print("  3:07 line:", l.strip()[:160])
        for tok in re.findall(r'(\S+\.(?:py|sh))', m.group(3)):
            if "llm-lock" in tok: continue
            for base in (os.path.join(WS,"skills/dreaming/scripts"), os.path.join(WS,"scripts")):
                cand = tok if os.path.isabs(tok) else os.path.join(base, os.path.basename(tok))
                if os.path.isfile(cand):
                    print(f"    {os.path.basename(tok)} -> EXISTS at {sh(cand)}"); break
            else:
                print(f"    {os.path.basename(tok)} -> not found in either scripts dir")
