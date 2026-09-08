#!/usr/bin/env python3
"""block_kiss_introspection.py — Aegis. Block KISS from introspection's reflective prompt (keep blush, keep the
kiss subsystem itself untouched). Removes the '=== RECENT KISSES ===' and '=== KISS LEDGER ===' sections from
the context heredoc and drops the word 'kisses' from the read-through instruction. Backup + abort-clean."""
import os, time, shutil
P = os.path.expanduser("~/Vintos/introspection.sh")
if not os.path.isfile(P): print("introspection.sh not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")
orig = list(lines)

def remove_section(hdr):
    idx = [i for i, l in enumerate(lines) if l.strip() == hdr]
    if len(idx) != 1:
        print(f"  ! '{hdr}' x{len(idx)} (want 1) — skipped"); return False
    i = idx[0]; j = i + 1
    while j < len(lines) and lines[j].strip() != "" and not lines[j].strip().startswith("==="):
        j += 1
    del lines[i:j]
    print(f"  - removed section '{hdr}' ({j-i} lines)")
    return True

changes = 0
# 1. drop 'kisses' from the read-through instruction (keep everything else)
for i, l in enumerate(lines):
    if "dreams, journals, kisses" in l:
        lines[i] = l.replace(", kisses", ""); changes += 1
        print("  - dropped 'kisses' from read-through instruction"); break
# 2. remove the two kiss sections from the context
if remove_section("=== RECENT KISSES ==="): changes += 1
if remove_section("=== KISS LEDGER ==="): changes += 1

if changes < 2:
    print(f"only {changes} change(s) — aborting, nothing written."); raise SystemExit(1)
if lines == orig:
    print("no change produced — aborting."); raise SystemExit(1)

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write("\n".join(lines))
print(f"OK — introspection no longer feeds kiss into reflection (blush kept). backup: {bak}")
print(f"revert: cp {bak} {P}")
