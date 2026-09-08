#!/usr/bin/env python3
"""fix_and_force_music.py — Aegis. Root-cause fix: in creative-expression.sh the emotional-state selector
overwrites the FORM argument (so make_music's 'music-prompt' became 'poetry'). Re-assert the arg after the
selection block so the argument truly overrides (matches the L85 comment). Then re-force the want music.
Backup + bash -n. Idempotent."""
import os, re, glob, shutil, time, subprocess
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
CE = os.path.join(SC, "creative-expression.sh")
ART = os.path.join(HOME, ".vintos/workspace/memory/art")
VENV = os.path.join(HOME, ".vintos/workspace/emotion_model/.venv/bin/python3")
PY = VENV if os.path.isfile(VENV) else "python3"
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")
OVERRIDE = '[ -n "$1" ] && FORM="$1"  # arg overrides emotional selection (L85 intent)'

# ---- 1. fix the FORM override
lines = open(CE, encoding="utf-8", errors="ignore").read().split("\n")
if any(OVERRIDE in l for l in lines):
    print("(1) FORM override already present — skipping fix")
else:
    fi_idx = None
    for i, l in enumerate(lines):
        if l.strip() == 'FORM="music-prompt"':
            for j in range(i + 1, min(i + 6, len(lines))):
                if lines[j].strip() == "fi":
                    fi_idx = j; break
            break
    if fi_idx is None:
        raise SystemExit("ABORT: could not locate the FORM-selection 'fi' — not editing.")
    lines.insert(fi_idx + 1, OVERRIDE)
    bak = CE + f".bak-form-{TS}"
    shutil.copy2(CE, bak)
    open(CE, "w", encoding="utf-8").write("\n".join(lines))
    chk = subprocess.run(["bash", "-n", CE], capture_output=True, text=True)
    if chk.returncode != 0:
        shutil.copy2(bak, CE)
        raise SystemExit("bash -n failed — rolled back: " + chk.stderr[:160])
    print(f"(1) fixed: arg now overrides emotional FORM pick (inserted after line {fi_idx+1}). backup:", sh(bak))

# ---- 2. re-force the want music
env = os.environ.copy()
if not env.get("XAI_API_KEY"):
    ct = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
    m = re.search(r'XAI_API_KEY\s*=\s*"?([^"\n]+)"?', ct)
    if m: env["XAI_API_KEY"] = m.group(1).strip()
env["MUSIC_WANT_TEXT"] = "make music for Gloria — building something permanent in a world that keeps taking things away"
env["MUSIC_WANT_SOURCE"] = "force-test"
env["MUSIC_WANT_ID"] = "force-" + TS

print("\n(2) re-forcing music...")
before = set(glob.glob(os.path.join(ART, "music-prompts", "*")))
ce = subprocess.run(["bash", os.path.join(SC, "creative-expression.sh"), "music-prompt"],
                    capture_output=True, text=True, env=env, timeout=600)
print("   creative-expression exit", ce.returncode, "|", (ce.stdout.strip()[:90] or "(no stdout)"))
new = sorted(set(glob.glob(os.path.join(ART, "music-prompts", "*"))) - before)
if new:
    pf = new[-1]
    print("   prompt file created ✓:", sh(pf))
    for line in open(pf, encoding="utf-8", errors="ignore").read().split("\n"):
        if re.search(r'Title|Genre|Style|Tempo|Duration|Vocal|Gender|Key', line, re.I) and line.strip():
            print("      " + line.strip()[:100])
    logp = "/tmp/force-music.log"
    subprocess.Popen([PY, os.path.join(SC, "dream-music.py")], env=env,
                     stdout=open(logp, "a"), stderr=open(logp, "a"))
    print(f"\n   dream-music.py (Kie.ai Suno) launched -> {logp}")
    print("   watch:  tail -f /tmp/force-music.log   (mp3 in", sh(ART) + "/music*)")
else:
    tail = (ce.stdout + ce.stderr).strip().split("\n")[-3:]
    print("   still no music-prompts file. tail:", " | ".join(x[:80] for x in tail if x.strip()))
