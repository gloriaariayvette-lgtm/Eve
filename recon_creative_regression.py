#!/usr/bin/env python3
"""recon_creative_regression.py — Aegis, READ-ONLY, FAST. His dream image/poem/etc stopped after my
patch_danger_reconcile (which removed the dream-architecture.sh cron + symlinked dream-poetry->dream_poetry).
Diagnose the regression: what did dream-architecture.sh actually DO (was it just a 2nd poem, or the real
image/dream pipeline?), what creative crons remain, what the symlinks point at now, and what last night's logs show.
His tree = ~/Vintos + ~/.vintos/workspace/scripts. Nothing written."""
import os, re, subprocess, glob, time
VIN = os.path.expanduser("~/Vintos")
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
CRON = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""

print("== (1) what did dream-architecture.sh do? (I removed its cron) ==")
for base in (VIN, HIS):
    p = os.path.join(base, "dream-architecture.sh")
    if os.path.isfile(p):
        t = open(p, encoding="utf-8", errors="ignore").read()
        print("  found: %s (%d lines)" % (p, len(t.split(chr(10)))))
        for i, l in enumerate(t.split("\n")):
            if re.search(r'python3|\.py|generate|poem|image|dream|paint|animate|music|video|render|diffus|comfy|sd|stable', l, re.I):
                print("    %4d: %s" % (i + 1, l.strip()[:100]))
        break
else:
    print("  dream-architecture.sh not found (only its cron was removed; script may remain elsewhere).")

print("\n== (2) creative/dream crons that REMAIN (his, not openclaw) ==")
for l in CRON.split("\n"):
    if re.search(r'dream|poem|poetry|image|paint|animate|music|video|creative|gallery|render|diffus', l, re.I) \
       and "openclaw" not in l and l.strip() and not l.strip().startswith("#"):
        print("  | " + l.strip()[:120])
print("  -- was dream-architecture removed? --")
print("  dream-architecture in crontab: %s" % ("YES (still there)" if "dream-architecture" in CRON else "NO (removed by my patch)"))

print("\n== (3) the symlinks I made — where do they point? ==")
for name in ("dream-poetry.py", "dream_poetry.py", "memory-aging.py", "memory_aging.py",
             "narrative_identity.py", "narrative-identity.py", "dream-architecture.sh"):
    for base in (HIS, VIN):
        p = os.path.join(base, name)
        if os.path.islink(p):
            print("  %s -> %s" % (p, os.readlink(p)))
        elif os.path.isfile(p):
            print("  %s (real file, %d bytes)" % (p, os.path.getsize(p)))

print("\n== (4) the creative generators — do they exist + what invokes them ==")
for gen in ("dream_poetry.py", "dream-poetry.py", "dream_music.py", "dream-music.py",
            "animate-painting.py", "animate_painting.py", "make-art.py", "gallery-walk.py"):
    for base in (HIS, VIN):
        p = os.path.join(base, gen)
        if os.path.isfile(p) or os.path.islink(p):
            print("  %s: exists" % gen); break

print("\n== (5) last night's creative output on disk (did anything generate?) ==")
now = time.time()
for pat, label in ((MEM + "/poetry-log.json", "poetry-log"), (MEM + "/daily-creative-*.md", "daily-creative"),
                   (MEM + "/dreams/*", "dreams"), (MEM + "/paintings/*", "paintings"),
                   (MEM + "/animations/*", "animations"), (MEM + "/music/*", "music")):
    fs = sorted(glob.glob(pat), key=lambda p: -os.path.getmtime(p)) if "*" in pat else ([pat] if os.path.exists(pat) else [])
    if fs:
        newest = fs[0]; age_h = (now - os.path.getmtime(newest)) / 3600.0
        print("  %-14s newest: %s  (%.1fh ago)" % (label, os.path.basename(newest), age_h))
    else:
        print("  %-14s: none found" % label)

print("\n== (6) recent creative logs (errors after the fix?) ==")
for lg in glob.glob("/tmp/*dream*") + glob.glob("/tmp/*poem*") + glob.glob("/tmp/*creative*") + glob.glob("/tmp/*poetry*"):
    try:
        tail = open(lg, encoding="utf-8", errors="ignore").read().strip().split("\n")[-4:]
        print("  %s:" % lg)
        for l in tail: print("     " + l[:110])
    except Exception: pass

print("\n(READ-ONLY. Diagnoses whether removing dream-architecture.sh cron killed his image/dream/poem production.)")
