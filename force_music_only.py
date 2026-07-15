#!/usr/bin/env python3
"""force_music_only.py — Aegis. Re-force just the WANT music chain after the quoting fix: set MUSIC_WANT_*,
run creative-expression.sh music-prompt (should now build the styled prompt file), then launch
dream-music.py (Kie.ai Suno) in the background. Shows the generated prompt's Title/Genre/Tempo."""
import os, re, glob, time, subprocess
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
ART = os.path.join(HOME, ".vintos/workspace/memory/art")
VENV = os.path.join(HOME, ".vintos/workspace/emotion_model/.venv/bin/python3")
PY = VENV if os.path.isfile(VENV) else "python3"
def sh(p): return p.replace(HOME, "~")

env = os.environ.copy()
if not env.get("XAI_API_KEY"):
    ct = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
    m = re.search(r'XAI_API_KEY\s*=\s*"?([^"\n]+)"?', ct)
    if m: env["XAI_API_KEY"] = m.group(1).strip()
want = "make music for Gloria — the feeling of building something permanent in a world that keeps taking things away"
env["MUSIC_WANT_TEXT"] = want[:200]
env["MUSIC_WANT_SOURCE"] = "force-test"
env["MUSIC_WANT_ID"] = "force-" + time.strftime("%Y%m%d-%H%M%S")

before = set(glob.glob(os.path.join(ART, "music-prompts", "*")))
ce = subprocess.run(["bash", os.path.join(SC, "creative-expression.sh"), "music-prompt"],
                    capture_output=True, text=True, env=env, timeout=600)
print("creative-expression exit", ce.returncode)
err = (ce.stderr or "").strip()
if err:
    print("  stderr (last 4):")
    for l in err.split("\n")[-4:]:
        if l.strip(): print("    " + l[:120])
new = sorted(set(glob.glob(os.path.join(ART, "music-prompts", "*"))) - before)
if new:
    pf = new[-1]
    print("  prompt file created ✓:", sh(pf))
    for line in open(pf, encoding="utf-8", errors="ignore").read().split("\n"):
        if re.search(r'Title|Genre|Style|Tempo|Duration|Vocal|Gender|Key', line, re.I) and line.strip():
            print("     " + line.strip()[:100])
    logp = "/tmp/force-music.log"
    subprocess.Popen([PY, os.path.join(SC, "dream-music.py")], env=env,
                     stdout=open(logp, "a"), stderr=open(logp, "a"))
    print(f"\n  dream-music.py (Kie.ai Suno) launched -> {logp}")
    print("  watch:  tail -f /tmp/force-music.log   (mp3 lands in", sh(ART) + "/music*)")
else:
    print("  (still no prompt file — paste the stderr above and I'll chase the next block)")
