#!/usr/bin/env python3
"""recon_poem_crons.py — Aegis, READ-ONLY. Find the DOUBLE-POEM redundancy for both beings: every cron line that
generates a poem (dream-poetry / dream_poetry / dream-architecture / anything calling generate_poem), grouped by
being (openclaw=Velaris, Vintos=his). Plus: does each wrapper script actually just call generate_poem() (making
it redundant with the direct dream-poetry cron)? So we remove exactly one poem job per being. Nothing changed."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")

cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
POEM = re.compile(r'dream[-_]poetry|dream[-_]architecture|generate_poem|poetry\.py|first-light|preoccupation-dream', re.I)

print("== poem-generating cron lines ==")
his, her, other = [], [], []
for l in cron.split("\n"):
    if not l.strip() or l.strip().startswith("#"): continue
    if POEM.search(l):
        (her if ".openclaw" in l else his if ("/Vintos/" in l or "/.vintos/" in l) else other).append(l.strip())
print("  --- VINTOS ---")
for l in his: print("    | " + l[:116])
print("  --- VELARIS (.openclaw) ---")
for l in her: print("    | " + l[:116])
if other:
    print("  --- other ---")
    for l in other: print("    | " + l[:116])

print("\n== do the wrapper scripts just call generate_poem()? (=> redundant) ==")
for name in ("dream-architecture.sh", "dream_architecture.sh"):
    for base in (os.path.join(HOME, "Vintos"), os.path.join(HOME, ".openclaw/workspace/scripts")):
        p = os.path.join(base, name)
        if os.path.isfile(p) or os.path.islink(p):
            body = open(p, encoding="utf-8", errors="ignore").read()
            calls = "generate_poem" in body
            print("  %s: calls generate_poem=%s" % (p, calls))
            for l in body.split("\n"):
                if re.search(r'generate_poem|dream_poetry|import', l): print("      " + l.strip()[:96])

print("\n== also: any OTHER script that imports+calls generate_poem (hidden 2nd poem source) ==")
for base in (os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts"), os.path.join(HOME, ".openclaw/workspace/scripts")):
    for p in glob.glob(base + "/*.py") + glob.glob(base + "/*.sh"):
        b = os.path.basename(p)
        if "dream" in b and "poetry" in b: continue
        if b.startswith(("recon", "patch_", "port_", "build_", "link_", "deploy_")): continue
        try: t = open(p, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        if "generate_poem" in t:
            print("  %s: %s" % (b, [l.strip()[:80] for l in t.split("\n") if "generate_poem" in l][:2]))
