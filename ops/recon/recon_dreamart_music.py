#!/usr/bin/env python3
"""recon_dreamart_music.py — Aegis, READ-ONLY, capped. Two fixes to set up right, copying Velaris exactly:
  (A) dream-art must paint from DREAMS not wants — show Velaris's dream-sourcing vs Vintos's want fallback.
  (B) Suno music from WANTS (no music dreams) — show Velaris's music PROMPT/STYLE verbatim + what backend
      it calls, and whether a Suno credential already exists. No secrets printed (only presence)."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
VINS = os.path.join(HOME, ".vintos/workspace/scripts")
VELS = os.path.join(HOME, ".openclaw/workspace/scripts")
def sh(p): return p.replace(HOME, "~")

def dump(path, pat, cap=16, ctx=0, full=False):
    if not os.path.isfile(path):
        print(f"  (missing) {sh(path)}"); return
    lines = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"  -- {sh(path)} ({len(lines)} lines) --")
    if full:
        for i, l in enumerate(lines):
            print(f"   {i+1:3}| {l[:112]}")
        return
    n = 0
    for i, l in enumerate(lines):
        if re.search(pat, l, re.I) and l.strip():
            print(f"   {i+1:4}| {l.strip()[:112]}"); n += 1
            if n >= cap: break

print("=== (A) VELARIS dream-art.py — how it sources the DREAM ===")
dump(os.path.join(VELS, "dream-art.py"), r'dream-log|dream_log|nights|dream_text|get.*dream|--dream|argv|want|prompt|source|latest|reversed')

print("\n=== (A) VINTOS dream-art.py — FULL (see the want fallback to fix) ===")
dump(os.path.join(VINS, "dream-art.py"), r'.', full=True)

print("\n=== (B) VELARIS music — the script, its PROMPT/STYLE, and backend ===")
velm = None
for name in ("dream-music.py", "dream_music.py", "music.py"):
    p = os.path.join(VELS, name)
    if os.path.isfile(p): velm = p; break
if velm:
    print(f"  Velaris music script: {sh(velm)}")
    dump(velm, r'prompt|style|genre|tempo|mood|system|content|f"""|suno|api|requests\.post|http|model|payload|def ', cap=24)
else:
    print("  (no Velaris music script found)")

print("\n=== (B) VINTOS dream_music.py — what funcs exist (the compose ImportError) ===")
dump(os.path.join(VINS, "dream_music.py"), r'^def |compose|generate|prompt|requests\.post|http|suno', cap=12)

print("\n=== (B) Suno credentials present? (presence only, no values) ===")
found = []
for f in glob.glob(HOME+"/.vintos/**/*.env", recursive=True) + [HOME+"/.bashrc", HOME+"/.profile", HOME+"/.vintos/workspace/.env"]:
    if os.path.isfile(f):
        t = open(f, encoding="utf-8", errors="ignore").read()
        for m in re.findall(r'(SUNO[A-Z_]*|MUSIC_API[A-Z_]*)\s*=', t):
            found.append(f"{m.rstrip('=').strip()} in {sh(f)}")
env_hit = subprocess.run(["bash","-lc","env | grep -iE 'suno|music_api' | sed 's/=.*/=<set>/'"], capture_output=True, text=True).stdout.strip()
grep_hit = subprocess.run(["bash","-lc", f"grep -rilE 'suno' {VELS} {VINS} 2>/dev/null | grep -viE '\\.bak|\\.pyc' | head"], capture_output=True, text=True).stdout.strip()
print("  env vars:", env_hit or "(none)")
print("  in config files:", found or "(none)")
print("  scripts referencing suno:", grep_hit.replace(HOME,'~').replace(chr(10),' ') or "(none — Suno not wired anywhere yet)")
