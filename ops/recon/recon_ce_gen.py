#!/usr/bin/env python3
"""recon_ce_gen.py — Aegis, READ-ONLY. Why does creative-expression.sh music-prompt exit 0 but write no
file? Show: (1) all case labels + does 'music-prompt' match one, (2) the music case body (USER_PROMPT +
OUTDIR), (3) the generation call (LM_API) and the FILE-WRITE step (OUTPUT_FILE / > $ART_DIR). Verbatim."""
import os, re
HOME = os.path.expanduser("~")
CE = os.path.join(HOME, ".vintos/workspace/scripts/creative-expression.sh")
lines = open(CE, encoding="utf-8", errors="ignore").read().split("\n")

print("=== (1) case labels (what FORM values are handled) ===")
in_case = False
for i, l in enumerate(lines):
    if re.match(r'\s*case\s+"?\$FORM', l): in_case = True
    if in_case and re.match(r'\s*"?[A-Za-z0-9_-]+"?\)\s*$', l):
        print(f"   {i+1:4}| {l.strip()}")
    if in_case and re.match(r'\s*esac', l): print(f"   {i+1:4}| esac"); break
print("   >>> wants-router calls it with arg: 'music-prompt'")

print("\n=== (2) the FORM/arg handling (how $1 becomes FORM) ===")
for i, l in enumerate(lines):
    if re.search(r'FORM=|^\s*\[ -n "\$1"|case .*FORM', l) and l.strip():
        print(f"   {i+1:4}| {l.strip()[:100]}")

print("\n=== (3) generation call + file write (OUTPUT_FILE / OUTDIR / > $ART_DIR / LM_API POST) ===")
for i, l in enumerate(lines):
    if re.search(r'OUTPUT_FILE|OUTDIR|ART_DIR|LM_API|curl |requests\.post|>\s*"?\$ART|TIMESTAMP|mkdir|RESPONSE=|SYSTEM_PROMPT=|\.txt|\.md|write', l) \
       and l.strip() and not l.strip().startswith("#"):
        print(f"   {i+1:4}| {l.strip()[:120]}")
