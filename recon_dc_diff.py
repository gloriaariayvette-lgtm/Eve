#!/usr/bin/env python3
"""recon_dc_diff.py — Aegis, READ-ONLY. Stop theorizing: read today's daily-creative (broken) vs recent working
days, show each file's section headers + sizes, so the sections MISSING today name exactly what broke. Then grep
which script writes the missing header. Nothing written."""
import os, re, glob, datetime
MEM = os.path.expanduser("~/.vintos/workspace/memory")
VIN = os.path.expanduser("~/Vintos")
HIS = os.path.expanduser("~/.vintos/workspace/scripts")

dcs = sorted(glob.glob(os.path.join(MEM, "daily-creative-*.md")), reverse=True)[:5]
print("== recent daily-creative files ==")
for p in dcs:
    print("  %s  (%d bytes)" % (os.path.basename(p), os.path.getsize(p)))

def headers(p):
    t = open(p, encoding="utf-8", errors="ignore").read()
    hs = [l.strip() for l in t.split("\n") if l.strip().startswith("#") or re.match(r'\*\*.+\*\*', l.strip())]
    return t, hs

print("\n== section headers per day (missing-today = broken) ==")
allheaders = {}
for p in dcs:
    t, hs = headers(p)
    d = os.path.basename(p).replace("daily-creative-", "").replace(".md", "")
    print("\n  --- %s (%d bytes) ---" % (d, len(t)))
    for h in hs[:20]: print("     %s" % h[:90])
    for h in hs: allheaders.setdefault(h.split("—")[0].strip()[:40], set()).add(d)

if len(dcs) >= 2:
    today = os.path.basename(dcs[0]).replace("daily-creative-", "").replace(".md", "")
    _, htoday = headers(dcs[0])
    htoday_norm = {h.split("—")[0].strip()[:40] for h in htoday}
    print("\n== headers seen on OTHER days but NOT today (%s) ==" % today)
    missing = []
    for h, days in allheaders.items():
        if today not in days and h not in htoday_norm and len(h) > 2:
            print("   MISSING: %-40s (seen on: %s)" % (h, ", ".join(sorted(days))[:40]))
            missing.append(h)

    # today full dump (it's short if broken)
    print("\n== today's daily-creative FULL content ==")
    print(open(dcs[0], encoding="utf-8", errors="ignore").read()[:1800])

    # who writes the missing headers?
    print("\n== which script writes each missing header ==")
    for h in missing:
        key = re.sub(r'[^A-Za-z ]', '', h).strip()
        if len(key) < 4: continue
        for base in (VIN, HIS):
            for e in os.scandir(base) if os.path.isdir(base) else []:
                if not e.is_file() or not e.name.endswith((".py", ".sh")): continue
                try: t = open(e.path, encoding="utf-8", errors="ignore").read()
                except Exception: continue
                if "daily-creative" in t and key.split()[0] in t:
                    # confirm it writes (append) with that header text
                    if re.search(re.escape(key.split()[0]), t) and re.search(r'daily-creative.*(a["\']|append|>>|"a"|\'a\')|open\([^)]*daily-creative[^)]*["\']a', t):
                        print("   '%s' <- %s" % (h[:34], e.name)); break

print("\n(READ-ONLY. Missing-today sections + their writer = the exact break.)")
