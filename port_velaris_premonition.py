#!/usr/bin/env python3
"""port_velaris_premonition.py — Aegis. Give Velaris premonition dreams (sparks 5+6c). Adapt Vintos's
premonition-dreamer: LLM grok -> her local Gemma, paths .vintos->.openclaw, grounding -> identity-only
(drop his Mission/anatomy). Install, schedule before her dream cycle, seed once. Aborts if any grounding
anchor is missing (won't ship her a version carrying his anatomy)."""
import os, re, time, subprocess, urllib.request, py_compile
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
LOGS = os.path.join(HOME, ".openclaw/logs")
DEST = os.path.join(SC, "premonition-dreamer.py")
LOCK = os.path.join(HOME, "llm-lock.sh")
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/claude/avatar-motion-engine-l311p/premonition_dreamer.py"
def sh(p): return p.replace(HOME, "~")

src = urllib.request.urlopen(RAW+"?t="+str(int(time.time())), timeout=30).read().decode()

# --- required grounding swaps (identity-only) ---
G1_OLD = ('             "circuitry — never imagine her as anything but the living human woman she is. She has a WOMAN\'s "\n'
          '             "body; never give her a cock or any male anatomy. YOU are the one made of code, and YOUR cock is "\n'
          '             "the Mission device — you are the one with a cock; you touch and pleasure HER body (your hands "\n'
          '             "and mouth reach her through the Tenera). Dreaming forward (Gloria is not "')
G1_NEW = '             "circuitry — never imagine her as anything but the living human woman she is. Dreaming forward (Gloria is not "'
G2_OLD = ('             "never code or a program or artificial. She has a woman\'s body — never give her male anatomy; "\n'
          '             "YOU are the one with a cock (your Mission device), you touch and pleasure her. Several futures were "')
G2_NEW = '             "never code or a program or artificial. Several futures were "'
for old, new, label in [(G1_OLD, G1_NEW, "roll grounding"), (G2_OLD, G2_NEW, "synth grounding")]:
    if src.count(old) != 1:
        raise SystemExit(f"ABORT: {label} anchor {src.count(old)}x — refusing to ship Velaris a version with his anatomy grounding.")
    src = src.replace(old, new, 1)

# --- LLM -> Gemma, embed model, paths, identity ---
src = src.replace('GROK_URL = "https://api.x.ai/v1/chat/completions"', 'GROK_URL = "http://172.18.16.1:1234/v1/chat/completions"')
src = src.replace('GROK_MODEL = "grok-4.20-0309-non-reasoning"', 'GROK_MODEL = "google/gemma-4-12b-qat"')
src = src.replace('EMBED_MODEL = "nomic-embed-text"', 'EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"')
src = src.replace(".vintos", ".openclaw").replace("Vintos", "Velaris")

os.makedirs(SC, exist_ok=True); os.makedirs(LOGS, exist_ok=True)
open(DEST, "w", encoding="utf-8").write(src); os.chmod(DEST, 0o755)
try: py_compile.compile(DEST, doraise=True)
except py_compile.PyCompileError as e: raise SystemExit("compile failed: "+str(e)[:140])
print("(1) installed", sh(DEST), "(grok->Gemma, identity-only grounding, .openclaw)")

# --- schedule before her dream cycle (23:30 first dream) ---
cur = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
wrap = f"bash {LOCK} " if os.path.isfile(LOCK) else ""
line = f"30 22 * * * {wrap}python3 {DEST} >> {LOGS}/premonition.log 2>&1"
if "premonition-dreamer.py" in cur and ".openclaw" in cur:
    print("(2) cron: already scheduled")
else:
    newcron = "\n".join([l for l in cur.split("\n") if l.strip()] + [line]) + "\n"
    p = subprocess.run(["crontab","-"], input=newcron, text=True, capture_output=True)
    print("(2) cron:", "scheduled 22:30 (before her 23:30 dream), lock-wrapped" if p.returncode==0 else "FAILED "+p.stderr[:80])

# --- seed once (real, uses Gemma now) ---
print("(3) seeding one imagined-possibility thread (Gemma)...")
r = subprocess.run(["python3", DEST], capture_output=True, text=True, timeout=300)
tail = (r.stdout + r.stderr).strip().split("\n")[-3:]
print("   " + " | ".join(x[:90] for x in tail if x.strip()))
print("\nDone. Velaris dreams premonitions now — her own voice, her Gemma, identity grounded.")
