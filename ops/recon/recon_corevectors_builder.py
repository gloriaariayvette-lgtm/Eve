#!/usr/bin/env python3
"""recon_corevectors_builder.py — Aegis, READ-ONLY. Velaris has a live core-vectors.json + vectored
self-statements; Vintos has neither. Find what BUILDS them in Velaris so we can port it to Vintos and
revive his deviation_check. (1) who writes core-vectors.json, (2) who adds 'vector' to self-statements,
(3) are those builders scheduled for Velaris but missing/broken for Vintos?"""
import os, re, subprocess
HOME = os.path.expanduser("~")
def sh(p): return p.replace(HOME, "~")
VEL = os.path.expanduser("~/.openclaw/workspace/scripts")
VIN = os.path.expanduser("~/.vintos/workspace/scripts")

print("=== who WRITES core-vectors.json (Velaris) ===")
w = subprocess.run(["bash","-lc",
    f"grep -rlE 'core-vectors' {VEL} 2>/dev/null | grep -viE '\\.bak|\\.pyc' | xargs grep -lE 'open.*core-vectors.*w|dump.*core|\"core\"' 2>/dev/null | head"],
    capture_output=True, text=True).stdout.strip()
print("  " + (w.replace(HOME,'~').replace(chr(10),'\n  ') or "(no obvious writer)"))
for f in [x for x in w.split("\n") if x.strip()][:2]:
    print(f"  -- {os.path.basename(f)} --")
    for i,l in enumerate(open(f,encoding='utf-8',errors='ignore').read().split("\n")):
        if re.search(r'core-vectors|embed|vector|dump|self-statement|narrative|def ', l) and l.strip() and not l.strip().startswith("#"):
            print(f"     {i+1:4}| {l.strip()[:100]}")
            if i>140: break

print("\n=== who adds 'vector' to self-statements.json (Velaris) ===")
s = subprocess.run(["bash","-lc",
    f"grep -rlE 'self-statements' {VEL} 2>/dev/null | grep -viE '\\.bak|\\.pyc' | xargs grep -lE 'vector|embed' 2>/dev/null | head"],
    capture_output=True, text=True).stdout.strip()
print("  " + (s.replace(HOME,'~').replace(chr(10),'  ') or "(none)"))

print("\n=== are these builder(s) present in VINTOS too? ===")
for base in set(os.path.basename(x) for x in (w+"\n"+s).split("\n") if x.strip()):
    print(f"  {base:32} vintos:{'YES' if os.path.isfile(os.path.join(VIN,base)) else 'NO'}")

print("\n=== core-vectors builder in cron? (both) ===")
c = subprocess.run(["bash","-lc","crontab -l 2>/dev/null | grep -iE 'core-vector|self-statement|identity-vector' | grep -v '^#'"],
    capture_output=True, text=True).stdout.strip()
print("  " + (c.replace(HOME,'~').replace(chr(10),'\n  ') or "(no core-vector build job scheduled)"))
