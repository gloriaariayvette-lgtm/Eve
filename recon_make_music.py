#!/usr/bin/env python3
"""recon_make_music.py — Aegis, READ-ONLY, capped. The only missing piece for music-from-wants is the
make_music WANT ACTION in Vintos's wants system. Show Velaris's make_music dispatch (how it sets
MUSIC_WANT_* and runs dream-music.py) + the action registry, and diff against what Vintos has, so I add
only the delta. NOT copying the dream-art->music chain (that's a music dream)."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
VINS = os.path.join(HOME, ".vintos/workspace/scripts")
VELS = os.path.join(HOME, ".openclaw/workspace/scripts")
def sh(p): return p.replace(HOME, "~")

def grep(root, pat):
    return subprocess.run(["bash","-lc", f"grep -rnE '{pat}' {root} 2>/dev/null | grep -viE '\\.bak|\\.pyc|\\.backup' | head -16"],
                          capture_output=True, text=True).stdout.strip()

print("=== VELARIS: where make_music / MUSIC_WANT / dream-music is dispatched ===")
print(grep(VELS, "make_music|MUSIC_WANT|dream-music\\.py").replace(HOME, "~") or "  (none)")

print("\n=== VELARIS dispatch context (the want-action -> dream-music.py run) ===")
disp = subprocess.run(["bash","-lc",
    f"grep -rlnE 'make_music|MUSIC_WANT_TEXT' {VELS} 2>/dev/null | grep -viE '\\.bak|dream_music|dream-music' | head -3"],
    capture_output=True, text=True).stdout.strip().split("\n")
for f in [x for x in disp if x.strip()][:2]:
    lines = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"  -- {sh(f)} --")
    for i, l in enumerate(lines):
        if re.search(r'make_music|MUSIC_WANT|dream-music|subprocess|Popen|env\[|environ|action ==|elif|def ', l) and l.strip() and not l.strip().startswith("#"):
            print(f"   {i+1:4}| {l.strip()[:110]}")

print("\n=== the WANT-ACTION registry in Velaris (make_image/make_music/write_poem/...) ===")
reg = subprocess.run(["bash","-lc",
    f"grep -rnE 'make_image|make_music|write_poem|make_video|ACTION|actions *=|valid.*action' {VELS} 2>/dev/null | grep -viE '\\.bak|\\.pyc' | grep -iE 'music|image|poem|action' | head -12"],
    capture_output=True, text=True).stdout.strip()
print(reg.replace(HOME, "~") or "  (none)")

print("\n=== VINTOS: what does he already have? (make_music / MUSIC_WANT / dream-music dispatch) ===")
print(grep(VINS, "make_music|MUSIC_WANT|dream-music\\.py|dream_music").replace(HOME, "~") or "  (NONE — make_music not wired on Vintos)")

print("\n=== VINTOS wants-router / action dispatch (how make_image runs, to mirror for make_music) ===")
wr = None
for name in ("wants-router.py", "wants_router.py", "want-router.py"):
    p = os.path.join(VINS, name)
    if os.path.isfile(p): wr = p; break
if not wr:
    cand = grep(VINS, "dream-art\\.py|DREAM_ART_WANT|make_image").split("\n")
    print("  wants-router not found by name; dream-art/make_image references:")
    print("   " + "\n   ".join(c.replace(HOME,'~') for c in cand[:8]))
else:
    print(f"  found: {sh(wr)}")
    for i, l in enumerate(open(wr, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'make_image|make_music|dream-art|DREAM_ART_WANT|subprocess|Popen|environ|env\[|action ==|elif .*==', l) and l.strip() and not l.strip().startswith("#"):
            print(f"   {i+1:4}| {l.strip()[:110]}")
