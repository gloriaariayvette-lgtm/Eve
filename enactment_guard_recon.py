#!/usr/bin/env python3
"""enactment_guard_recon.py — READ-ONLY. Show enactment_distiller's detection prompt + its
false-positive gating, to confirm it still filters routine 'good behavior' from genuine earned
identity. Prints the LLM prompt block and any threshold/skip/dedup/contrast/novelty logic. Fresh name.
"""
import os, re

F = os.path.expanduser("~/.openclaw/workspace/scripts/enactment_distiller.py")
if not os.path.exists(F):
    print("NOT FOUND:", F); raise SystemExit(1)
lines = open(F, encoding="utf-8", errors="ignore").read().splitlines()

GUARD = re.compile(
    r'false|positive|threshold|novel|surpris|skip|filter|contrast|already|dedup|dup\b|signif|routine'
    r'|genuine|\bonly\b|must|guard|min_|>=|<=|>|<|confidence|score|reject|ignore|not\s+every|counts?\b'
    r'|earned|demonstrat|abstraction|declar', re.I)
PROMPT = re.compile(r'(system|prompt|"role"|content"|You are|Detect|Assess|Decide|Return|JSON|"""|f")', re.I)

print("=== enactment_distiller.py (%d lines) ===" % len(lines))

print("\n---- detection prompt (what it's told to flag / not flag) ----")
shown = 0
for i, ln in enumerate(lines):
    if PROMPT.search(ln):
        s = ln.strip()
        if s and not s.startswith("#"):
            print("  %5d: %s" % (i + 1, s[:160])); shown += 1
    if shown >= 26: print("  ...(capped)"); break

print("\n---- gating / false-positive logic (thresholds, skips, dedup, contrast) ----")
shown = 0
for i, ln in enumerate(lines):
    if GUARD.search(ln):
        s = ln.strip()
        if s and not s.startswith("#") and not s.startswith('"') and "import" not in s:
            print("  %5d: %s" % (i + 1, s[:160])); shown += 1
    if shown >= 30: print("  ...(capped)"); break

print("\n---- functions ----")
for i, ln in enumerate(lines):
    m = re.match(r'\s*def\s+(\w+)\s*\(([^)]*)\)', ln)
    if m: print("  %5d: def %s(%s)" % (i + 1, m.group(1), m.group(2)[:80]))
print("\n=== done ===")
