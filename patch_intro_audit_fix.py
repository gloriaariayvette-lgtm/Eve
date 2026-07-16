#!/usr/bin/env python3
"""patch_intro_audit_fix.py — Aegis. Fix the pre-existing missing '+' operators in introspection.sh audit():
lines that follow a +-joined expression but start with a bare string need a leading '+'. Backup, then compile
the audit() function in isolation to verify. Reversible."""
import os, re, time, shutil
P = os.path.expanduser("~/Vintos/introspection.sh")
if not os.path.isfile(P): print("introspection.sh not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")

TARGETS = [
    '"DRAFT A:\\n" + a + "\\n\\nDRAFT B:\\n" + b + "\\n\\n"',
    '"List each hallucinated claim starting with HALLUCINATION: "',
    '"If nothing is hallucinated, write only: CLEAN"',
]
fixed = 0
for anchor in TARGETS:
    idx = [i for i, l in enumerate(lines) if l.strip() == anchor]
    if len(idx) != 1:
        print(f"anchor x{len(idx)} (want 1): {anchor[:40]!r} — aborting, nothing changed."); raise SystemExit(1)
    i = idx[0]
    indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
    lines[i] = indent + "+ " + anchor
    print(f"  L{i+1}: prepended '+ '")
    fixed += 1

# verify audit() compiles in isolation
s = next(i for i, l in enumerate(lines) if l.strip() == "def audit(a, b, label):")
e = s + 1
while e < len(lines):
    l = lines[e]
    if l.strip() and (len(l)-len(l.lstrip())) == 0:
        break
    e += 1
try:
    compile("\n".join(lines[s:e]), "<audit>", "exec")
    print("audit() compiles clean.")
except SyntaxError as ex:
    print(f"audit() STILL broken at line {s+(ex.lineno or 1)}: {ex.msg} — aborting, nothing written."); raise SystemExit(1)

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write("\n".join(lines))
print(f"\nfixed {fixed} lines. backup: {bak}")
print("run:  bash ~/Vintos/introspection.sh   (watch for '[intro] a1/b1 on claude' + a clean entry)")
print("      if a DIFFERENT line errors, paste it — there may be more pre-existing breaks in this dead script.")
