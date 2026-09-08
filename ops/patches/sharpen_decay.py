#!/usr/bin/env python3
"""sharpen_decay.py — shorten emotion decay half-lives so Connection/Warmth stop pinning high and
Groundedness eases a touch. Connection/Warmth x0.5, Groundedness x0.75. Backup + restart daemon.
Aborts (shows raw) if the list isn't a clean literal. Aegis."""
import os, re, ast, shutil, time, subprocess
HOME = os.path.expanduser("~")
def run(a): return subprocess.run(a, capture_output=True, text=True)

CFG = os.path.expanduser("~/.vintos/workspace/emotion_model/config.py")
if not os.path.isfile(CFG):
    found = run(["bash","-lc","grep -rln 'DECAY_HALF_LIVES *=' ~/.vintos/workspace ~/Vintos 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head -1"]).stdout.strip()
    CFG = found or CFG
print("config:", CFG.replace(HOME, "~"))
body = open(CFG, encoding="utf-8").read()

DIMS = ["Valence","Arousal","Dominance","Safety","Desire","Connection",
        "Playfulness","Curiosity","Warmth","Tension","Groundedness"]
FACTOR = {"Connection": 0.5, "Warmth": 0.5, "Groundedness": 0.75}

m = re.search(r'DECAY_HALF_LIVES\s*=\s*(\[[^\]]*\])', body, re.S)
if not m:
    print("!! DECAY_HALF_LIVES literal not found"); raise SystemExit(1)
raw = m.group(1)
print("\nraw DECAY_HALF_LIVES:\n ", raw.strip()[:300])
try:
    vals = ast.literal_eval(raw)
    assert isinstance(vals, list) and len(vals) == len(DIMS)
except Exception as e:
    print("\n!! not a clean 11-item literal (%s) — aborting so I can hand-edit exactly." % e); raise SystemExit(2)

new = list(vals)
print("\nchanges (half-life in hours; smaller = sharper decay):")
for name, f in FACTOR.items():
    i = DIMS.index(name)
    old = new[i]; new[i] = round(float(old) * f, 3)
    print(f"  {name:12} {old}  ->  {new[i]}")

new_list = "[" + ", ".join(repr(v) for v in new) + "]"
new_body = body[:m.start(1)] + new_list + body[m.end(1):]
bak = CFG + ".bak-decay-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(CFG, bak)
open(CFG, "w", encoding="utf-8").write(new_body)
# syntax check
sc = run(["python3","-c", f"import ast; ast.parse(open('{CFG}').read())"])
if sc.returncode != 0:
    shutil.copy2(bak, CFG); print("!! syntax error — rolled back:", sc.stderr[:150]); raise SystemExit(2)
print("\nwritten. backup:", bak.replace(HOME,'~'))

run(["bash","-lc","systemctl --user restart vintos-emoclaw.service"])
time.sleep(3)
act = run(["bash","-lc","systemctl --user is-active vintos-emoclaw.service"]).stdout.strip()
print("emoclaw daemon:", act, "(state persists across restart)")
print("Connection/Warmth now fall ~2x faster toward baseline; Groundedness a touch faster.")
