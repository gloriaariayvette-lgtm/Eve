#!/usr/bin/env python3
"""patch_journal_bilateral_ban.py — Aegis. The journal final leaked its drafting process ('both versions of me
… both named the same'). Add a hard ban to _synthesis_system: never reference drafts/versions/combining — the
entry is one voice, hers to read. Backup + abort-clean. Reversible."""
import os, time, shutil
P = os.path.expanduser("~/Vintos/idle-journal.sh")
if not os.path.isfile(P): print("idle-journal.sh not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")
if any("NEVER reference your drafting process" in l for l in lines):
    print("already patched — aborting."); raise SystemExit(0)

ANCHOR = '_synthesis_system += "\\n\\nWrite no more than 800 words."'
idx = [i for i, l in enumerate(lines) if l.strip() == ANCHOR]
if len(idx) != 1:
    print(f"anchor x{len(idx)} (want 1) — aborting, nothing changed."); raise SystemExit(1)
i = idx[0]; ind = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
BAN = (ind + '_synthesis_system += "\\n\\nNEVER reference your drafting process. Do not write '
       "'two drafts', 'both drafts', 'both versions of me', 'the other version', 'combining', or say that you "
       'wrote, absorbed, or reconciled anything. The reader is Gloria. The entry is one voice — yours. Write as '
       'a single self, not as a system integrating parts."')
lines[i+1:i+1] = [BAN]

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write("\n".join(lines))
print(f"OK — journal final can no longer narrate the bilateral process. backup: {bak}")
print(f"revert: cp {bak} {P}")
