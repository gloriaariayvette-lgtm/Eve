#!/usr/bin/env python3
"""recon_session_map.py — Aegis, READ-ONLY. Print session_map.py in full + show where it's called from
(server.py / inner_context.py / anywhere), and the ARC file it writes, so we can say precisely what it is."""
import os, re, glob
HOME = os.path.expanduser("~")
P = os.path.expanduser("~/.vintos/workspace/scripts/session_map.py")

print("===== session_map.py (full) =====")
if os.path.isfile(P):
    for i, l in enumerate(open(P, encoding="utf-8", errors="ignore").read().split("\n")):
        print(f"{i+1:>3}: {l}")
else:
    print("  NOT FOUND")

print("\n===== who calls session_map (import / get_session_arc / session_map) =====")
roots = [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")]
rx = re.compile(r'session_map|session[_-]?arc|SESSION ARC', re.I)
for d in roots:
    for p in glob.glob(os.path.join(d, "*.py")) + glob.glob(os.path.join(d, "*.sh")):
        if os.path.basename(p) == "session_map.py": continue
        try: L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        except Exception: continue
        for i, l in enumerate(L):
            if rx.search(l):
                print(f"  {os.path.basename(p)}:{i+1}: {l.strip()[:100]}")
