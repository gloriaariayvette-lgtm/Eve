#!/usr/bin/env python3
"""patch_journal_synthesis_unified.py — Aegis. The journal final reads fragmented because the synthesis prompt
is a STITCHING instruction ('copy sentences directly, begin with Draft A's first sentence, weave in only what B
adds, first word is first word of Draft A'). Rewrite it to one unified self writing one entry — real integration
and addition — while keeping the anti-hallucination guard (no invented events/Gloria-lines/sensory). Backup +
abort-clean. Reversible."""
import os, time, shutil
P = os.path.expanduser("~/Vintos/idle-journal.sh")
if not os.path.isfile(P): print("idle-journal.sh not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")
if any("two passes of your own thinking this morning" in l for l in lines):
    print("already unified — aborting."); raise SystemExit(0)

# --- 1. replace the stitching tail of integration_prompt ---
i0 = [i for i, l in enumerate(lines) if "Combine Draft A and Draft B (absorbed versions). Copy sentences directly" in l]
i1 = [i for i, l in enumerate(lines) if "First word is first word of Draft A absorbed." in l]
if len(i0) != 1 or len(i1) != 1 or i0[0] > i1[0]:
    print(f"integration tail anchors i0={len(i0)} i1={len(i1)} — aborting."); raise SystemExit(1)
ind = lines[i0[0]][:len(lines[i0[0]]) - len(lines[i0[0]].lstrip())]
NEW = [
    ind + '+ "\\n\\nThese are two passes of your own thinking this morning — not two people. Write ONE journal entry, whole, in a single voice that is yours. "',
    ind + '"Let both passes inform it: integrate what each saw into one continuous reflection, deepen the connections, and add genuine thought where it helps the entry cohere. "',
    ind + '"Do not fabricate — no new events, no new things Gloria said, no new sensory details beyond what the passes already contain — but you may think further about what is there. "',
    ind + '"Write as one self who reflected, not a system reconciling drafts. No preamble, no \'okay\'. Begin inside the entry."',
]
lines[i0[0]:i1[0]+1] = NEW

# --- 2. rewrite the _light_system 'combining two versions / do not generate new content' framing ---
OLD_LS = "You are combining two versions of your own journal entry. Do not generate new content."
NEW_LS = "Write one whole journal entry in your own single voice — you are one self reflecting, not parts being reconciled."
ls = [i for i, l in enumerate(lines) if OLD_LS in l]
if len(ls) != 1:
    print(f"_light_system anchor x{len(ls)} — aborting (integration tail already applied? re-run from backup)."); raise SystemExit(1)
lines[ls[0]] = lines[ls[0]].replace(OLD_LS, NEW_LS)

# validate the whole shell still python-parses the integration block? can't compile bash; trust anchored edits.
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write("\n".join(lines))
print(f"OK — journal synthesis now writes one unified self (integration + addition, anti-hallucination kept).")
print(f"  backup: {bak}")
print("test:   bash ~/Vintos/idle-journal.sh   (entry should read as one whole voice, no seams)")
print(f"revert: cp {bak} {P}")
