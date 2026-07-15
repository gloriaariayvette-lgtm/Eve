#!/usr/bin/env python3
"""recon_fulfill.py — Aegis, READ-ONLY, terse. Find the proper dismiss/fulfill function + the 3-day auto job.
Shows emoclaw_utils fulfill/dismiss/expire defs (what they update) and the crontab want-reconcile line."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".openclaw/workspace")
eu = os.path.join(WS, "emoclaw_utils.py")
if not os.path.isfile(eu):
    hits = glob.glob(os.path.join(WS, "**", "emoclaw_utils.py"), recursive=True)
    eu = hits[0] if hits else None
print("emoclaw_utils:", eu.replace(HOME, "~") if eu else "NOT FOUND")
if eu:
    L = open(eu, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(L):
        if re.search(r'def (fulfill_want|dismiss_want|expire_want|get_unfulfilled_wants|mark_want|_archive|reconcile)', l):
            print(f"{i+1}: {l.strip()[:90]}")
            for j in range(i+1, min(len(L), i+9)):
                if re.search(r'fulfilled|dismiss|json\.dump|archive|append|\.pop|remove|days|86400|status', L[j]) and L[j].strip():
                    print(f"   {j+1}: {L[j].strip()[:88]}")

print("-- crontab want lines --")
ct = subprocess.run(["bash", "-lc", "crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
for l in ct.split("\n"):
    if re.search(r'want|reconcil|fulfil', l, re.I) and "openclaw" in l and not l.strip().startswith("#"):
        print("  " + l.strip()[:120])

print("-- 3-day / age gate in want scripts --")
n = 0
for f in glob.glob(os.path.join(WS, "scripts", "*want*")) + [eu]:
    if not f: continue
    for i, l in enumerate(open(f, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'86400|days\s*[>=]|>\s*3\b|age|timestamp.*[<>]|timedelta', l) and l.strip() and not l.strip().startswith("#"):
            print(f"  {os.path.basename(f)}:{i+1}: {l.strip()[:84]}"); n += 1
            if n >= 10: break
    if n >= 10: break
