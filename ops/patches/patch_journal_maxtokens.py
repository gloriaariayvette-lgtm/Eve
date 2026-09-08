#!/usr/bin/env python3
"""patch_journal_maxtokens.py — Aegis. Fix idle-journal.sh Claude calls: reasoning=True with max_tokens=1500
lets adaptive thinking consume the whole budget -> empty output -> grok fallback. Give headroom (final 6000,
a1/b1 3000) and print stop_reason on empty. Backup + abort-clean. Reversible."""
import os, time, shutil
P = os.path.expanduser("~/Vintos/idle-journal.sh")
if not os.path.isfile(P): print("idle-journal.sh not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")

out, changed = [], 0
i = 0
while i < len(lines):
    l = lines[i]
    if "_claude_sync(_synthesis_system, integration_prompt, True)" in l and "max_tokens" not in l:
        out.append(l.replace("integration_prompt, True)", "integration_prompt, True, max_tokens=6000)")); changed += 1
    elif "_claude_sync(system_msg, user_msg, True)" in l and "max_tokens" not in l:
        out.append(l.replace("user_msg, True)", "user_msg, True, max_tokens=3000)")); changed += 1
    elif l.strip() == "return (_t or None), _th":
        ind = l[:len(l) - len(l.lstrip())]
        out.append(ind + "if not _t:")
        out.append(ind + "    import sys as _es; print('[claude_sync] empty out; stop=' + str(_d.get('stop_reason')) + ' err=' + str(_d.get('error'))[:200], file=_es.stderr, flush=True)")
        out.append(ind + "return (_t or None), _th")
        changed += 1
    else:
        out.append(l)
    i += 1

if changed < 3:
    print(f"only {changed} edits matched (want >=3) — aborting, nothing changed."); raise SystemExit(1)
newtext = "\n".join(out)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(newtext)
print(f"OK — {changed} edits (final=6000, a1/b1=3000, empty-print). backup: {bak}")
print("run:  bash ~/Vintos/idle-journal.sh   (expect '[journal] final on claude')")
