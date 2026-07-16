#!/usr/bin/env python3
"""patch_journal_middle_gemma.py — Aegis. idle-journal.sh's a1/b1 + final are _claude_sync (Claude-direct,
untouched). Every OTHER LLM call (audit1, absorb, held, audit_r, integration, audit2, post-passes, fallbacks)
was swept onto the shim's Claude route by the fleet swap; per spec those are Gemma. Repoint them to the shim's
/gemma route (URL-only; the shim forces the Gemma model + grok fallback). Backup + abort-clean. Reversible."""
import os, time, shutil
P = os.path.expanduser("~/Vintos/idle-journal.sh")
if not os.path.isfile(P): print("idle-journal.sh not found"); raise SystemExit(1)
txt = open(P, encoding="utf-8").read()
OLD = "http://127.0.0.1:8599/v1/chat/completions"
NEW = "http://127.0.0.1:8599/gemma/v1/chat/completions"
if "/gemma/v1/chat/completions" in txt:
    print("already redirected — aborting."); raise SystemExit(0)
n = txt.count(OLD)
if n == 0:
    print("no shim URLs found (journal not swapped?) — aborting."); raise SystemExit(1)
new = txt.replace(OLD, NEW)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
print(f"OK — {n} journal middle/after calls repointed to Gemma (a1/b1 + final stay Claude via _claude_sync).")
print(f"  backup: {bak}")
print(f"revert: cp {bak} {P}")
