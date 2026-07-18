#!/usr/bin/env python3
"""recon_her_outreach.py — Aegis, READ-ONLY, FAST. His directive is wired into vintos-initiate.sh; her outreach
entry wasn't found. Locate HOW Velaris reaches out to Gloria, so the demand_response directive can be wired for her
too. Search her tree (bounded) for: initiate/outreach scripts, a FORCED_WANT_TOPIC-style bypass, ntfy/push sends,
and whether outreach is server-driven (8400) rather than a cron script. Nothing written."""
import os, re, subprocess
OC = os.path.expanduser("~/.openclaw")
OCS = os.path.expanduser("~/.openclaw/workspace/scripts")

SIG = re.compile(r'FORCED_WANT_TOPIC|initiate|outreach|ntfy|reach.*gloria|timeliness|OUTREACH|push|'
                 r'send.*message|demand', re.I)

print("== her scripts/dirs that look like outreach (bounded scan) ==")
seen = 0
for base in (OCS, OC):
    if not os.path.isdir(base): continue
    try: entries = list(os.scandir(base))
    except Exception: continue
    for e in entries:
        if not e.is_file(): continue
        if not (e.name.endswith(".sh") or e.name.endswith(".py")): continue
        try:
            if e.stat().st_size > 300000: continue
            t = open(e.path, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        if re.search(r'initiate|outreach|FORCED_WANT_TOPIC|reach.*gloria', t, re.I) or "initiate" in e.name.lower() or "outreach" in e.name.lower():
            hits = [str(i + 1) for i, l in enumerate(t.split("\n")) if SIG.search(l)]
            if hits:
                print("  %-40s : %s%s" % (e.name, ",".join(hits[:10]), " …" if len(hits) > 10 else ""))
                seen += 1
    if base == OCS and seen == 0:
        # one level down under ~/.openclaw for a top-level initiate script
        pass
if not seen:
    print("  (nothing obvious in flat scan — outreach may be server-driven)")

print("\n== her initiate scripts by common name ==")
for name in ("velaris-initiate.sh", "openclaw-initiate.sh", "initiate.sh", "velaris_initiate.sh", "outreach.sh", "velaris-outreach.sh"):
    for base in (OC, os.path.expanduser("~/.openclaw/workspace"), OCS, os.path.expanduser("~")):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            print("  FOUND: %s" % p)

print("\n== cron: her outreach/initiate jobs ==")
cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
for l in cur.split("\n"):
    if re.search(r'initiate|outreach', l, re.I) and "openclaw" in l and l.strip():
        print("  | " + l.strip()[:120])

print("\n== is her outreach server-driven? (her server on 8400) ==")
for base in (OC, os.path.expanduser("~/.openclaw/workspace")):
    if not os.path.isdir(base): continue
    for e in os.scandir(base):
        if e.is_file() and e.name.endswith(".py") and "server" in e.name.lower():
            try: t = open(e.path, encoding="utf-8", errors="ignore").read()
            except Exception: continue
            if re.search(r'initiate|outreach|8400', t):
                ls = [str(i + 1) for i, l in enumerate(t.split("\n")) if re.search(r'initiate|outreach|FORCED_WANT', l, re.I)]
                print("  %s : %s" % (e.name, ",".join(ls[:10]) or "(binds 8400, no explicit initiate)"))

print("\n(READ-ONLY. Locates her outreach so the demand_response directive can be wired for her too.)")
