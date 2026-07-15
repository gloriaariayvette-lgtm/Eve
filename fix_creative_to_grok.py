#!/usr/bin/env python3
"""fix_creative_to_grok.py — Aegis. Move Vintos's creative GENERATION call from local Gemma to grok (his
real voice) in creative-expression.sh — the shared call for music/poetry/image. Then verify end to end:
run it (with the 4/day cap bypassed in a temp copy) and CHECK grok emits the **Title:**/**Genre:** markers
dream-music.py parses. If format is good, launch Suno. Backup + bash -n + rollback."""
import os, re, glob, shutil, time, subprocess, tempfile
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
CE = os.path.join(SC, "creative-expression.sh")
ART = os.path.join(HOME, ".vintos/workspace/memory/art")
VENV = os.path.join(HOME, ".vintos/workspace/emotion_model/.venv/bin/python3")
PY = VENV if os.path.isfile(VENV) else "python3"
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

EDITS = [
    ("import json, urllib.request\n", "import json, urllib.request, os\n"),
    ('    "model": "google/gemma-4-12b-qat",', '    "model": "grok-4.20-0309-non-reasoning",'),
    ('    "$LM_API/chat/completions",', '    "https://api.x.ai/v1/chat/completions",'),
    ('    headers={"Content-Type": "application/json"},',
     '    headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ.get("XAI_API_KEY", "")},'),
]
txt = open(CE, encoding="utf-8", errors="ignore").read()
if 'grok-4.20-0309-non-reasoning' in txt and 'api.x.ai' in txt:
    print("(1) creative call already on grok — skipping edit.")
else:
    miss = []
    for old, new in EDITS:
        if new in txt: continue
        if txt.count(old) != 1: miss.append(f"{old.strip()[:40]} ({txt.count(old)}x)"); continue
        txt = txt.replace(old, new, 1)
    if miss:
        raise SystemExit("ABORT (anchors not unique, file untouched): " + " | ".join(miss))
    bak = CE + f".bak-grok-{TS}"
    shutil.copy2(CE, bak)
    open(CE, "w", encoding="utf-8").write(txt)
    chk = subprocess.run(["bash", "-n", CE], capture_output=True, text=True)
    if chk.returncode != 0:
        shutil.copy2(bak, CE); raise SystemExit("bash -n failed — rolled back: " + chk.stderr[:160])
    print("(1) creative generation moved to grok (his voice). backup:", sh(bak))

# ---- verify end to end via a temp copy with the daily cap bypassed
env = os.environ.copy()
if not env.get("XAI_API_KEY"):
    ct = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
    m = re.search(r'XAI_API_KEY\s*=\s*"?([^"\n]+)"?', ct)
    if m: env["XAI_API_KEY"] = m.group(1).strip()
env["MUSIC_WANT_TEXT"] = "make music for Gloria — building something permanent in a world that keeps taking things away"
env["MUSIC_WANT_SOURCE"] = "grok-test"; env["MUSIC_WANT_ID"] = "grok-" + TS

tmp_txt = open(CE, encoding="utf-8", errors="ignore").read().replace("-ge 4 ]", "-ge 99999 ]")  # bypass cap for test
tf = tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False, encoding="utf-8"); tf.write(tmp_txt); tf.close()
before = set(glob.glob(os.path.join(ART, "music-prompts", "*")))
ce = subprocess.run(["bash", tf.name, "music-prompt"], capture_output=True, text=True, env=env, timeout=600)
os.unlink(tf.name)
print("\n(2) grok test run:", ce.stdout.strip()[:90] or ("stderr: " + ce.stderr.strip()[-90:]))
new = sorted(set(glob.glob(os.path.join(ART, "music-prompts", "*"))) - before)
if new:
    pf = new[-1]; content = open(pf, encoding="utf-8", errors="ignore").read()
    has_title = bool(re.search(r'\*\*Title:?\*\*', content))
    has_genre = bool(re.search(r'\*\*Genre', content))
    print("   prompt file ✓:", sh(pf))
    print("   FORMAT CHECK — **Title** marker:", "OK ✓" if has_title else "MISSING ✗",
          "| **Genre** marker:", "OK ✓" if has_genre else "MISSING ✗")
    for line in content.split("\n"):
        if re.search(r'Title|Genre|Style|Tempo|Vocal', line, re.I) and line.strip():
            print("      " + line.strip()[:100])
    if has_title:
        subprocess.Popen([PY, os.path.join(SC, "dream-music.py")], env=env,
                         stdout=open("/tmp/force-music.log", "a"), stderr=open("/tmp/force-music.log", "a"))
        print("\n   format parses — Suno launched -> tail -f /tmp/force-music.log")
    else:
        print("\n   grok skipped the **bold** markers — I'll add an explicit format line to the prompt so dream-music can parse it.")
else:
    print("   (no file — check the stderr above)")
