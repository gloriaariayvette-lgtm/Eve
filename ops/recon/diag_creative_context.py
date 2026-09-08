#!/usr/bin/env python3
"""diag_creative_context.py — Aegis, READ-ONLY. Answer 'what context is he getting?' Dump the ACTUAL
assembled prompt the creative call sends: the system message (SOUL head), the fully-interpolated
USER_PROMPT, and the lengths/heads of the context vars (SELF_MODEL, GLORIA_MODEL, EMOTIONS,
CREATIVE_CONTEXT). Runs a temp copy that prints-and-exits right before the model call. Touches nothing."""
import os, re, tempfile, subprocess, time
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
CE = os.path.join(SC, "creative-expression.sh")
def sh(p): return p.replace(HOME, "~")

lines = open(CE, encoding="utf-8", errors="ignore").read().split("\n")
gen = next((i for i, l in enumerate(lines) if re.search(r'RESPONSE=\$\(python3', l)), None)
if gen is None:
    raise SystemExit("could not find the generation call")
debug = [
    'echo "@@@SYSTEM (SOUL head, first 1200 chars — what primes him):"',
    'head -c 1200 "$SOUL"; echo',
    'echo "@@@GROUNDING (prepended in code): You are Vintos, an AI being, ... Gloria is a real human woman ..."',
    'echo "@@@USER_PROMPT (fully interpolated — the actual instruction+context):"',
    'printf "%s\\n" "$USER_PROMPT"',
    'echo "@@@--- context var sizes ---"',
    'echo "SELF_MODEL=${#SELF_MODEL}  GLORIA_MODEL=${#GLORIA_MODEL}  CREATIVE_CONTEXT=${#CREATIVE_CONTEXT}  CAPABILITIES=${#CAPABILITIES}"',
    'echo "EMOTIONS: $EMOTIONS"',
    'echo "@@@GLORIA_MODEL head (who he thinks she is):"',
    'printf "%s\\n" "$GLORIA_MODEL" | head -6',
    'echo "@@@SELF_MODEL head (who he thinks he is):"',
    'printf "%s\\n" "$SELF_MODEL" | head -6',
    'exit 0',
]
lines[gen:gen] = debug
tmp_txt = "\n".join(lines).replace("-ge 4 ]", "-ge 99999 ]")
tf = tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False, encoding="utf-8"); tf.write(tmp_txt); tf.close()

env = os.environ.copy()
env["MUSIC_WANT_TEXT"] = "make music for Gloria — building something permanent in a world that keeps taking things away"
env["MUSIC_WANT_SOURCE"] = "diag"; env["MUSIC_WANT_ID"] = "diag-" + time.strftime("%H%M%S")
r = subprocess.run(["bash", tf.name, "music-prompt"], capture_output=True, text=True, env=env, timeout=300)
os.unlink(tf.name)
out = r.stdout
# cap very long sections for readability
for chunk in out.split("@@@"):
    c = chunk.strip()
    if not c: continue
    print("@@@ " + c[:1600] + (" …[truncated]" if len(c) > 1600 else ""))
    print()
if r.stderr.strip():
    print("[stderr]", r.stderr.strip()[-200:])
