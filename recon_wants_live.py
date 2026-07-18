#!/usr/bin/env python3
"""recon_wants_live.py — Aegis, READ-ONLY. Which wants-router is LIVE? The patch hit wants_router.py (underscore);
confirm cron runs that one (not the hyphen copy), whether the two are identical, and which now carries the fix."""
import os, re, subprocess, hashlib
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")
A = os.path.join(V, "wants_router.py")   # underscore (patched)
B = os.path.join(V, "wants-router.py")   # hyphen

def info(p):
    if not os.path.isfile(p): return "MISSING"
    t = open(p, encoding="utf-8", errors="ignore").read()
    return "%s | %dL | md5 %s | tell_gloria=%s" % (
        os.path.basename(p), len(t.splitlines()),
        hashlib.md5(t.encode()).hexdigest()[:8], "YES" if "def tell_gloria" in t else "no")

print("== the two copies ==")
print("  A:", info(A))
print("  B:", info(B))
print("  identical:", os.path.isfile(A) and os.path.isfile(B) and
      hashlib.md5(open(A, 'rb').read()).hexdigest() == hashlib.md5(open(B, 'rb').read()).hexdigest())

print("\n== crontab lines invoking a wants router ==")
cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
for l in cron.split("\n"):
    if re.search(r'wants[_-]router', l) and l.strip() and not l.strip().startswith("#"):
        print("  " + l.strip()[:120])

print("\n== who else imports/execs a wants router (scripts) ==")
import glob
for p in glob.glob(V + "/*.py") + glob.glob(V + "/*.sh") + glob.glob(os.path.expanduser("~/.vintos/workspace/scripts") + "/*.py"):
    b = os.path.basename(p)
    if b in ("wants_router.py", "wants-router.py") or b.startswith(("recon", "patch_", "port_", "build_")): continue
    try: t = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if re.search(r'wants[_-]router', t):
        for i, l in enumerate(t.split("\n")):
            if re.search(r'wants[_-]router', l): print("  %s:%d: %s" % (b, i + 1, l.strip()[:90])); break
