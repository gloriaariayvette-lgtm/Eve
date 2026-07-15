#!/usr/bin/env python3
"""patch_velaris_journal_thinking.py — Aegis. JOURNAL context ONLY (test bed before chat). Add
reasoning_effort:high to idle-journal.sh's call_llm() — which is a1/b1-only (absorb() is separate) — so the
bilateral first-passes reason. Reasoning lands in reasoning_content, NOT content, so the journal stays clean.
Scoped to call_llm(), backup + bash -n + rollback + idempotent. Prints the draft/journal paths to check."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")
if not os.path.isfile(P):
    raise SystemExit("not found: " + sh(P))
orig = open(P, encoding="utf-8", errors="ignore").read()

# scope to call_llm() body: from 'def call_llm():' to the next 'def '
i = orig.find("def call_llm():")
if i < 0:
    raise SystemExit("def call_llm() not found — structure changed, tell me")
m = re.search(r"\n\s*def\s", orig[i + 1:])
end = i + 1 + m.start() if m else i + 1500
seg = orig[i:end]

if "reasoning_effort" in seg:
    print("already applied — call_llm() already reasons."); raise SystemExit(0)
mm = re.search(r'"model":\s*"google/gemma-4-12b-qat",', seg)
if not mm:
    raise SystemExit("no gemma model line inside call_llm() — tell me")
new_seg = seg[:mm.end()] + '"reasoning_effort":"high",' + seg[mm.end():]
t = orig[:i] + new_seg + orig[end:]

bak = P + ".bak-vjournal-" + TS
shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(t)
chk = subprocess.run(["bash", "-n", P], capture_output=True, text=True)
if chk.returncode != 0:
    shutil.copy2(bak, P)
    raise SystemExit("bash -n FAILED — rolled back: " + chk.stderr[:160])
print("FIXED: idle-journal call_llm() now sends reasoning_effort:high (a1/b1 reason).")
print("backup:", sh(bak))

# show where to look when testing
print("\n--- what to check after a test run ---")
for l in t.split("\n"):
    if re.search(r'open\("/tmp/.*bilateral.*a1|open\("/tmp/.*bilateral.*b1|journal.*\.md|memory/.*journal|>>?\s*"?\$?\w*journal', l, re.I) and l.strip():
        print("  ", l.strip()[:110])
print("\nTest:  bash ~/.openclaw/workspace/scripts/idle-journal.sh   (watch it finish + read the journal it writes)")
print("Confirm: journal reads clean/coherent (content NOT flooded with reasoning) — that's the whole test.")
