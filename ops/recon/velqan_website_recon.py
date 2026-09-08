#!/usr/bin/env python3
"""velqan_website_recon.py — READ-ONLY, capped. How Velaris's website surfaces velqan/vocab (static
markup vs fetch from an endpoint) and whether velaris-server exposes an API — so Stage 3 renders the
shared coinage log the right way. Aegis."""
import os, re, subprocess
HOME = os.path.expanduser("~")
WEB = os.path.expanduser("~/velaris-server/website")
SRV = os.path.expanduser("~/velaris-server/server.py")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout

print("=== website: velqan/vocab surface (how it's shown + any fetch) ===")
for f in ("index.html", "app.html", "app/index.html"):
    p = os.path.join(WEB, f)
    if not os.path.isfile(p): continue
    ls = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"\n-- {f} --"); n=0
    for i,l in enumerate(ls):
        if re.search(r'velqan|vocab|lexicon|coinage|fetch\(|/api/|getElementById\([\'"][^\'"]*vocab', l, re.I):
            print(f"  {i+1:4}| {l.strip()[:150]}"); n+=1
            if n>=12: break

print("\n=== velaris-server: is it a live server with an API? (velqan endpoints?) ===")
if os.path.isfile(SRV):
    ls = open(SRV, encoding="utf-8", errors="ignore").read().split("\n")
    for i,l in enumerate(ls):
        if re.search(r'@app\.(get|post)\(|velqan|StaticFiles|mount\(|FileResponse|website', l, re.I):
            print(f"  {i+1:5}| {l.strip()[:130]}")
else:
    print("  (no velaris-server/server.py — website may be static/served elsewhere)")

print("\n=== is velaris-server running? on what port? ===")
print(" ", run(["bash","-lc","systemctl --user list-units --type=service 2>/dev/null | grep -iE 'velaris.*(server|web|site)' | head"]).strip() or "(no matching service)")
print(" ", run(["bash","-lc","ss -ltnp 2>/dev/null | grep -iE ':84|:80|velaris' | head -4"]).strip() or "")
