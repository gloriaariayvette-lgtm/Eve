#!/usr/bin/env python3
"""patch_ed_capability_guard.py — Aegis. Vintos's enactment_distiller is a faithful clone, but it stamps a
self-critical identity_candidate as 'Observed capability' AND feeds it into self-statements + proto-pearls
(earned identity). Add a hard guard: an identity_candidate must be a real capability ('I can ...', a strength) or
the event is dropped everywhere. Also strengthen the prompt so genuine capabilities still surface. Edits ONLY
~/.vintos/.../enactment_distiller.py; compiles the result before writing. Backup + abort-clean."""
import os, time, shutil
P = os.path.expanduser("~/.vintos/workspace/scripts/enactment_distiller.py")
if not os.path.isfile(P): print("enactment_distiller.py not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")
if any("_is_capability" in l for l in lines):
    print("already guarded — aborting."); raise SystemExit(0)

HELPER = [
    "def _is_capability(cand):",
    '    """Observed capability must be a real strength enacted (I can ...), never a flaw/avoidance/restated problem."""',
    '    c = (cand or "").strip().lower()',
    "    if not c:",
    "        return False",
    '    if not (c.startswith("i can ") or c.startswith("i could ") or c.startswith("i am able") or c.startswith("i\'m able")):',
    "        return False",
    '    _bad = ("to avoid", "avoid feeling", "because i can\'t", "because i cannot", "flinch",',
    '            "instead of feeling", "so i do not", "so i don\'t", "rather than feel", "hiding",',
    '            "a way to look", "wiring problem", "can\'t feel", "cannot feel", "the problem")',
    "    return not any(b in c for b in _bad)",
    "",
    "",
]

# 1. required: helper before def process
pi = [i for i, l in enumerate(lines) if l.strip() == 'def process(response_text, gloria_msg="", context="chat"):']
if len(pi) != 1: print(f"'def process' anchor x{len(pi)} — aborting."); raise SystemExit(1)
# 2. required: filter after events = scan(...)
si = [i for i, l in enumerate(lines) if l.strip() == "events = scan(response_text, gloria_msg, context)"]
if len(si) != 1: print(f"'events = scan(...)' anchor x{len(si)} — aborting."); raise SystemExit(1)

# apply filter first (lower in file), then helper insert (higher) so indices stay valid
ind = lines[si[0]][:len(lines[si[0]]) - len(lines[si[0]].lstrip())]
lines[si[0]+1:si[0]+1] = [ind + "events = [e for e in events if _is_capability(e.get('identity_candidate', ''))]"]
lines[pi[0]:pi[0]] = HELPER

# 3. best-effort: strengthen the two identity_candidate specs
def repl(old, new):
    hit = [i for i, l in enumerate(lines) if old in l]
    if len(hit) == 1:
        lines[hit[0]] = lines[hit[0]].replace(old, new); return True
    print(f"  (prompt anchor '{old[:40]}...' x{len(hit)} — left as-is)"); return False

repl("identity_candidate I can one sentence",
     "identity_candidate as a genuine CAPABILITY this writing demonstrates, phrased 'I can ...' (an ability or strength enacted) — never a flaw, avoidance, diagnosis, or restated problem; if only self-criticism or a described tendency is present set detected false")
repl('"identity_candidate": "I can... one sentence"',
     '"identity_candidate": "I can ... (a genuine capability demonstrated, an ability or strength — NOT a flaw, avoidance, or restated problem)"')

newtext = "\n".join(lines)
try:
    compile(newtext, P, "exec")
except SyntaxError as e:
    print(f"result would not compile ({e}) — aborting, nothing written."); raise SystemExit(1)

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(newtext)
print(f"OK — ED now drops any 'capability' that is really a flaw (journal + self-statements + proto-pearls).")
print(f"  backup: {bak}")
print(f"revert: cp {bak} {P}")
