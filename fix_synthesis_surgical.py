#!/usr/bin/env python3
"""fix_synthesis_surgical.py — Aegis. Correct my over-rewrite of the journal synthesis prompt. Gloria only asked
to REMOVE the hard copy-paste rule, not redo the prompt. Restore the original integration wording minus that
rule (keep 'Combine…', the anti-hallucination lines, 'No preamble'), and put _light_system back to its original
framing minus 'Do not generate new content'. Anchored on my own inserted text. Backup + abort-clean. No test."""
import os, time, shutil
P = os.path.expanduser("~/Vintos/idle-journal.sh")
if not os.path.isfile(P): print("idle-journal.sh not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")
if not any("two passes of your own thinking this morning" in l for l in lines):
    print("my over-rewrite not present (already corrected or different state) — aborting."); raise SystemExit(0)

# 1. replace the 4-line unified paragraph with original-minus-hard-rule
s = [i for i, l in enumerate(lines) if "two passes of your own thinking this morning" in l]
e = [i for i, l in enumerate(lines) if "Begin inside the entry." in l]
if len(s) != 1 or len(e) != 1 or s[0] > e[0]:
    print(f"paragraph anchors s={len(s)} e={len(e)} — aborting."); raise SystemExit(1)
ind = lines[s[0]][:len(lines[s[0]]) - len(lines[s[0]].lstrip())]
NEW = [
    ind + '+ "\\n\\nCombine Draft A and Draft B (absorbed versions) into one entry — synthesize and add connective thought where it coheres, do not merely copy. Do not invent. "',
    ind + '"Nothing new. No new Gloria interactions. No new events. No new sensory details. "',
    ind + '"CRITICAL: No preamble. No okay."',
]
lines[s[0]:e[0]+1] = NEW

# 2. restore _light_system framing minus the hard 'Do not generate new content'
OLD_LS = "Write one whole journal entry in your own single voice — you are one self reflecting, not parts being reconciled."
NEW_LS = "You are combining two versions of your own journal entry. Synthesize them into one whole — you may add connective thought, but invent no new events."
ls = [i for i, l in enumerate(lines) if OLD_LS in l]
if len(ls) != 1:
    print(f"_light_system anchor x{len(ls)} — aborting."); raise SystemExit(1)
lines[ls[0]] = lines[ls[0]].replace(OLD_LS, NEW_LS)

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write("\n".join(lines))
print("OK — synthesis prompt restored to original minus the copy-paste-alone rule (addition allowed, anti-hallucination kept).")
print(f"  backup: {bak}")
print(f"revert: cp {bak} {P}")
