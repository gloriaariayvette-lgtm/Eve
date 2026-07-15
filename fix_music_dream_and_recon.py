#!/usr/bin/env python3
"""fix_music_dream_and_recon.py — Aegis.
PART 1 (fix): actually remove the music-dream call from dream-architecture.sh (my last idempotency check
misfired). Backup + bash -n + rollback. Idempotent on presence of 'from dream_music import compose'.
PART 2 (recon, READ-ONLY): how Velaris triggers music FROM A WANT + its Kie.ai endpoint + key VAR NAME
(name only, never the value) + where music is saved/served — so Suno-from-wants copies Velaris exactly."""
import os, re, glob, shutil, time, subprocess
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
VELS = os.path.join(HOME, ".openclaw/workspace/scripts")
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

print("=== PART 1: remove music-dream call from dream-architecture.sh ===")
darch = os.path.join(SC, "dream-architecture.sh")
txt = open(darch, encoding="utf-8", errors="ignore").read()
if "from dream_music import compose" not in txt:
    print("  already gone — nothing to remove.")
else:
    new = txt.replace("\nfrom dream_music import compose\ncompose()", "", 1)
    if new == txt:
        # fallback: remove the two lines individually
        new = "\n".join(l for l in txt.split("\n") if l.strip() not in ("from dream_music import compose", "compose()"))
    bak = darch + f".bak-nomdream-{TS}"
    shutil.copy2(darch, bak)
    open(darch, "w", encoding="utf-8").write(new)
    r = subprocess.run(["bash","-n",darch], capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, darch)
        print("  syntax error — rolled back:", r.stderr[:120])
    else:
        print("  removed compose() music-dream call. backup:", sh(bak))

print("\n=== PART 2: how Velaris triggers music FROM A WANT ===")
callers = subprocess.run(["bash","-lc",
    f"grep -rnE 'dream.music|dream_music|generate\\(.*style|music' {VELS} 2>/dev/null | grep -viE '\\.bak|\\.pyc|def generate|^.*#' | head -18"],
    capture_output=True, text=True).stdout.strip()
print(callers.replace(HOME, "~") or "  (none)")

print("\n=== Velaris dream-music.py: endpoint, key VAR NAME (not value), save/serve ===")
vm = os.path.join(VELS, "dream-music.py")
if os.path.isfile(vm):
    for i, l in enumerate(open(vm, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'https?://|kie|api\.|environ\.get|API_KEY|Authorization|Bearer|BASE_URL|endpoint|save|\.mp3|gallery|music-log|def api|def poll|def generate', l, re.I) \
           and l.strip() and not l.strip().startswith("#"):
            # redact anything that looks like a literal key value
            ln = re.sub(r'("?)(sk-|key-|[A-Za-z0-9_\-]{24,})("?)', r'<redacted>', l.strip())
            print(f"   {i+1:4}| {ln[:112]}")

print("\n=== does Vintos's dream_music.py have the same key var wired? (name only) ===")
vv = os.path.join(SC, "dream_music.py")
if os.path.isfile(vv):
    for i, l in enumerate(open(vv, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'environ\.get|API_KEY|Authorization|Bearer|kie|https?://', l, re.I) and l.strip():
            ln = re.sub(r'("?)(sk-|key-|[A-Za-z0-9_\-]{24,})("?)', r'<redacted>', l.strip())
            print(f"   {i+1:4}| {ln[:110]}")

print("\n=== music key present in env? (presence only) ===")
env_hit = subprocess.run(["bash","-lc","env | grep -iE 'kie|suno|music' | sed 's/=.*/=<set>/'"], capture_output=True, text=True).stdout.strip()
print("  " + (env_hit or "(no kie/suno/music env var set in this shell)"))
