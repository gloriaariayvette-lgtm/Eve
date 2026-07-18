#!/usr/bin/env python3
"""recon_server_ports.py — Aegis, READ-ONLY. Confirm the discussion-board misroute: what PORT does each being's
server bind, what port does each wants-router POST discussion to, and which current-wants file the discussion
endpoint reads. If Vintos's server != 8400 but his wants-router posts to 8400, his discussions go to Velaris's
server (bug). Also locate Velaris's server."""
import os, re, glob
HOME = os.path.expanduser("~")

def ports_in(path):
    if not path or not os.path.isfile(path): return []
    t = open(path, encoding="utf-8", errors="ignore").read()
    out = []
    for m in re.finditer(r'uvicorn\.run\([^)]*port\s*=\s*(\d+)|\.run\([^)]*port\s*=\s*(\d+)|port\s*=\s*(\d{4})|:(\d{4})"', t):
        out += [g for g in m.groups() if g]
    return sorted(set(out))

print("== VINTOS server (~/Vintos/server.py) ==")
vs = os.path.join(HOME, "Vintos", "server.py")
print("  binds port(s):", ports_in(vs) or "?")
t = open(vs, encoding="utf-8", errors="ignore").read()
for m in re.finditer(r'(uvicorn\.run\(.{0,60}|app\.run\(.{0,60}|APP_PORT.{0,30}|PORT\s*=\s*\d+)', t):
    print("   ", m.group(0)[:80].replace("\n", " "))

print("\n== locate VELARIS server (serves /api/wants discussion, binds a port) ==")
for p in glob.glob(HOME + "/.openclaw/**/*.py", recursive=True):
    if "/backup" in p or "__pycache__" in p: continue
    try: t = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if "/api/wants" in t and "discussion" in t and ("uvicorn" in t or "FastAPI" in t or "app.run" in t):
        print("  %s  binds %s" % (p, ports_in(p) or "?"))

print("\n== which port does each wants-router POST discussion to ==")
for name, wr in (("VINTOS", os.path.join(HOME, "Vintos", "wants-router.py")),
                 ("VELARIS", os.path.join(HOME, ".openclaw/workspace/scripts/wants-router.py"))):
    if os.path.isfile(wr):
        t = open(wr, encoding="utf-8", errors="ignore").read()
        pts = sorted(set(re.findall(r'localhost:(\d+)/api/wants|127\.0\.0\.1:(\d+)/api/wants', t)))
        flat = sorted({x for tup in pts for x in tup if x})
        print("  %s wants-router posts /api/wants to port(s): %s" % (name, flat))

print("\n== Vintos server discussion endpoint: which wants file does it read? ==")
for i, l in enumerate(t.split("\n")):
    pass
S = open(vs, encoding="utf-8", errors="ignore").read().split("\n")
inblock = False
for i, l in enumerate(S):
    if re.search(r'def (get|post)_want_discussion|/api/wants/\{want_id\}/discussion', l): inblock = True; start = i
    if inblock and re.search(r'current-wants|discussion.*json|MEMORY|wants_path|open\(', l):
        print("  %d: %s" % (i + 1, l.strip()[:96]))
    if inblock and i > start + 30: inblock = False
