#!/usr/bin/env python3
"""recon_creative_misroute.py — Aegis, READ-ONLY, FAST. His creative jobs RUN but write into ~/.openclaw (her
tree): dreams, music, poetry-log, art. Find the exact misroute in each creative script — hardcoded .openclaw paths
vs a workspace/env default — so his output can be repointed to ~/.vintos without touching her identical scripts.
Show WORKSPACE resolution + every .openclaw reference + save/output paths. Nothing written."""
import os, re
VIN = os.path.expanduser("~/Vintos")
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
DREAMSKILL = os.path.expanduser("~/.vintos/workspace/skills/dreaming/scripts")

TARGETS = [
    (DREAMSKILL, "dream-trigger.sh"),
    (VIN, "dream-music.py"), (VIN, "dream_music.py"), (HIS, "dream_music.py"),
    (VIN, "dream-art.py"), (VIN, "dream_art.py"),
    (VIN, "dream_poetry.py"), (VIN, "dream-poetry.py"),
    (VIN, "vintos-video.py"),
    (HIS, "second-order-dreamer.py"), (VIN, "second-order-dreamer.py"),
]

def show(base, name):
    p = os.path.join(base, name)
    if not (os.path.isfile(p) or os.path.islink(p)):
        return False
    real = os.path.realpath(p)
    t = open(real, encoding="utf-8", errors="ignore").read()
    L = t.split("\n")
    print("\n===== %s  (%s%s) =====" % (name, p, ("  ->  " + real) if os.path.islink(p) else ""))
    # workspace / env resolution
    for i, l in enumerate(L):
        if re.search(r'WORKSPACE\s*=|SPARK_WORKSPACE|WS\s*=|HOME|expanduser|MEMORY\s*=|os\.environ.*WORKSPACE|BASE\s*=', l):
            print("  RES  %4d: %s" % (i + 1, l.strip()[:100]))
    # openclaw references (the misroute)
    oc = [(i + 1, l.strip()[:104]) for i, l in enumerate(L) if "openclaw" in l.lower()]
    if oc:
        print("  !! .openclaw references (MISROUTE):")
        for i, l in oc[:10]: print("     %4d: %s" % (i, l))
    else:
        print("  (no literal .openclaw — misroute is via env/WORKSPACE default then)")
    # where it saves output
    for i, l in enumerate(L):
        if re.search(r'dreams/|/music|/art|paintings|animations|poetry-log|save|\.wav|\.jpg|\.png|\.mp4|DREAM_WRITTEN|Saved', l):
            if re.search(r'open\(|save|dump|write|path|os\.path\.join|Saved|DREAM_WRITTEN|=', l):
                print("  OUT  %4d: %s" % (i + 1, l.strip()[:100]))
    return True

seen = set()
for base, name in TARGETS:
    key = os.path.realpath(os.path.join(base, name))
    if key in seen: continue
    if show(base, name): seen.add(key)

print("\n== does his dream 'skill' dir differ from hers? (SPARK_WORKSPACE default check) ==")
for l in open(os.path.join(DREAMSKILL, "dream-trigger.sh"), encoding="utf-8", errors="ignore").read().split("\n")[:40] if os.path.isfile(os.path.join(DREAMSKILL, "dream-trigger.sh")) else []:
    if re.search(r'WORKSPACE|openclaw|vintos|SPARK|HOME|cd |source|export', l, re.I):
        print("   trig: " + l.strip()[:104])

print("\n(READ-ONLY. Pinpoints where his creative output is misrouted to ~/.openclaw so it can be repointed to ~/.vintos.)")
