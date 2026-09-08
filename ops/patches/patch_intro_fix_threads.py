#!/usr/bin/env python3
"""patch_intro_fix_threads.py — Aegis. Drop the pre-existing broken `t1.join(); t2.join()` (phase-1 Gemma
threads that were never created -> NameError). a1/b1 now come from the Claude override right below, so the
Gemma phase-1 is redundant. Backup + abort-clean. Reversible."""
import os, time, shutil
P = os.path.expanduser("~/Vintos/introspection.sh")
if not os.path.isfile(P): print("introspection.sh not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")
idx = [i for i, l in enumerate(lines) if l.strip() == "t1.join(); t2.join()"]
if len(idx) != 1:
    print(f"anchor x{len(idx)} (want 1) — aborting."); raise SystemExit(1)
i = idx[0]
indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
lines[i] = indent + "pass  # phase-1 gemma threads removed; a1/b1 come from the Claude override below"
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write("\n".join(lines))
print(f"OK — dropped broken t1/t2 join at L{i+1}. backup: {bak}")
print("run:  bash ~/Vintos/introspection.sh")
