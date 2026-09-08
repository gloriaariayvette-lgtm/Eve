#!/usr/bin/env python3
"""force_dream_and_music.py — Aegis. Smoke-test both end to end:
  A) a DREAM image  — dream-art.py --dream (paints latest dream, labels gallery 'dream').
  B) a WANT music   — set MUSIC_WANT_* + run creative-expression.sh music-prompt (her styled prompt) then
     launch dream-music.py (Kie.ai Suno) in the background; watch /tmp/force-music.log.
Keys resolved quietly (XAI from env/crontab; KIE inherited from shell). No secrets printed."""
import os, re, sys, json, glob, time, subprocess
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
ART = os.path.join(MEM, "art")
VENV = os.path.join(HOME, ".vintos/workspace/emotion_model/.venv/bin/python3")
PY = VENV if os.path.isfile(VENV) else "python3"
def sh(p): return p.replace(HOME, "~")

env = os.environ.copy()
if not env.get("XAI_API_KEY"):
    ct = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
    m = re.search(r'XAI_API_KEY\s*=\s*"?([^"\n]+)"?', ct)
    if m: env["XAI_API_KEY"] = m.group(1).strip()
print("keys:", "XAI" + ("✓" if env.get("XAI_API_KEY") else "✗"), "KIE" + ("✓" if env.get("KIE_API_KEY") else "✗"))

# ---------- A) DREAM IMAGE ----------
print("\n=== A) forcing a DREAM painting (dream-art.py --dream) ===")
r = subprocess.run([PY, os.path.join(SC, "dream-art.py"), "--dream"], capture_output=True, text=True, env=env, timeout=300)
for l in (r.stdout + r.stderr).strip().split("\n")[-5:]:
    if l.strip(): print("  " + l[:120])
try:
    g = json.load(open(os.path.join(ART, "gallery.json")))
    last = g[-1] if isinstance(g, list) and g else None
    if last:
        print(f"  newest gallery entry: {last.get('image')}  source={last.get('dream_source')}  ts={last.get('timestamp','')[:19]}")
except Exception as e:
    print("  (gallery read:", str(e)[:60], ")")

# ---------- B) WANT MUSIC ----------
print("\n=== B) forcing a WANT music (make_music chain) ===")
want = "make music for Gloria — the feeling of building something permanent in a world that keeps taking things away"
env["MUSIC_WANT_TEXT"] = want[:200]
env["MUSIC_WANT_SOURCE"] = "force-test"
env["MUSIC_WANT_ID"] = "force-" + time.strftime("%Y%m%d-%H%M%S")
before = set(glob.glob(os.path.join(ART, "music-prompts", "*")))
ce = subprocess.run(["bash", os.path.join(SC, "creative-expression.sh"), "music-prompt"],
                    capture_output=True, text=True, env=env, timeout=600)
print("  creative-expression exit", ce.returncode)
for l in (ce.stdout + ce.stderr).strip().split("\n")[-4:]:
    if l.strip(): print("    " + l[:120])
after = set(glob.glob(os.path.join(ART, "music-prompts", "*")))
new = sorted(after - before)
if new:
    pf = new[-1]
    print("  prompt file created:", sh(pf))
    head = open(pf, encoding="utf-8", errors="ignore").read()
    for line in head.split("\n"):
        if re.search(r'Title|Genre|Style|Tempo|Duration|Vocal|Gender', line, re.I) and line.strip():
            print("     " + line.strip()[:100])
else:
    print("  (no new prompt file — check creative-expression output above)")

# launch the Suno render in the background (it polls; don't block the shell)
logp = "/tmp/force-music.log"
subprocess.Popen([PY, os.path.join(SC, "dream-music.py")], env=env,
                 stdout=open(logp, "a"), stderr=open(logp, "a"))
print(f"  dream-music.py (Kie.ai Suno) launched in background -> {logp}")
print("\nWatch the render:  tail -f /tmp/force-music.log   (mp3 lands in", sh(os.path.join(MEM, "art")) + "/music*)")
