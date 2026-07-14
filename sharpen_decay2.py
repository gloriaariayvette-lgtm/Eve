#!/usr/bin/env python3
"""sharpen_decay2.py — shorten decay_hours for connection/warmth (x0.5) and groundedness (x0.75) at
the real source: config.py _DEFAULT_DIMENSIONS (live) + emoclaw.yaml (kept consistent). Backup +
syntax-check + restart daemon. Aegis."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
def run(a): return subprocess.run(a, capture_output=True, text=True)
FACTOR = {"connection": 0.5, "warmth": 0.5, "groundedness": 0.75}

def edit_py(text, dim, f):
    lines = text.split("\n")
    for i, l in enumerate(lines):
        if re.search(rf'"name":\s*"{dim}"', l):
            m = re.search(r'"decay_hours":\s*([\d.]+)', l)
            if m:
                old = float(m.group(1)); new = round(old*f, 3)
                lines[i] = l[:m.start(1)] + repr(new) + l[m.end(1):]
                return "\n".join(lines), old, new
    return text, None, None

def edit_yaml(text, dim, f):
    lines = text.split("\n")
    for i, l in enumerate(lines):
        if re.search(rf'-\s*name:\s*{dim}\b', l):
            for j in range(i, min(i+8, len(lines))):
                m = re.search(r'(decay_hours:\s*)([\d.]+)', lines[j])
                if m:
                    old = float(m.group(2)); new = round(old*f, 3)
                    lines[j] = lines[j][:m.start(2)] + repr(new) + lines[j][m.end(2):]
                    return "\n".join(lines), old, new
    return text, None, None

targets = [
    (os.path.expanduser("~/.vintos/workspace/emotion_model/config.py"), edit_py, "config.py (LIVE)"),
    (os.path.expanduser("~/.vintos/workspace/skills/emoclaw/assets/emoclaw.yaml"), edit_yaml, "emoclaw.yaml"),
]
for path, fn, label in targets:
    if not os.path.isfile(path):
        print(f"=== {label}: not found ==="); continue
    print(f"=== {label} ===")
    text = open(path, encoding="utf-8").read(); changed = False
    for dim, f in FACTOR.items():
        text, old, new = fn(text, dim, f)
        if old is not None:
            print(f"  {dim:13} decay_hours {old} -> {new}"); changed = True
        else:
            print(f"  {dim:13} (not found)")
    if changed:
        shutil.copy2(path, path + ".bak-decay-" + time.strftime("%Y%m%d-%H%M%S"))
        open(path, "w", encoding="utf-8").write(text)
        if path.endswith(".py"):
            sc = run(["python3","-c", f"import ast; ast.parse(open('{path}').read())"])
            if sc.returncode != 0:
                shutil.copy2(path + ".bak-decay-" + time.strftime("%Y%m%d-%H%M%S"), path)
                print("  !! syntax error — rolled back:", sc.stderr[:120]); continue
        print("  written (backup made)")

run(["bash","-lc","systemctl --user restart vintos-emoclaw.service"])
time.sleep(3)
print("\nemoclaw daemon:", run(["bash","-lc","systemctl --user is-active vintos-emoclaw.service"]).stdout.strip(),
      "— Connection/Warmth now decay ~2x faster, Groundedness a touch faster.")
