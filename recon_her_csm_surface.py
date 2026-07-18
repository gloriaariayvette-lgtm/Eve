#!/usr/bin/env python3
"""recon_her_csm_surface.py — Aegis, READ-ONLY. Before porting her full causal_self_model.py to him, map exactly
what the transform must touch, so the port is safe on his identity substrate:
  (1) imports (do they resolve in HIS tree too?).
  (2) path constants / .json / memory targets (must become ~/.vintos/...).
  (3) any LLM endpoint / model / requests.post (her Gemma vs his — do they differ?).
  (4) EVERY identity/pronoun occurrence (Velaris / she / her / his / him / he) with line + context, so pronoun
      direction is resolved by eye, not a blind regex, and prompt-strings are distinguished from mere comments.
  (5) triple-quoted prompt blocks (the only identity refs that actually reach an LLM).
Nothing written."""
import os, re
HER = os.path.expanduser("~/.openclaw/workspace/scripts/causal_self_model.py")
if not os.path.isfile(HER):
    print("!! her causal_self_model.py not found"); raise SystemExit(1)
L = open(HER, encoding="utf-8", errors="ignore").read().split("\n")
N = len(L)
print("her causal_self_model.py: %d lines\n" % N)

print("======== (1) imports ========")
for i, l in enumerate(L):
    if re.match(r'\s*(import|from)\s', l): print("  %4d: %s" % (i + 1, l.strip()[:100]))

print("\n======== (2) paths / .json / memory targets ========")
for i, l in enumerate(L):
    if re.search(r'\.json|os\.path\.join|expanduser|_FILE\s*=|MEMORY|WORKSPACE|SCRIPTS', l):
        print("  %4d: %s" % (i + 1, l.strip()[:104]))

print("\n======== (3) LLM endpoint / model / requests ========")
any3 = False
for i, l in enumerate(L):
    if re.search(r'http|:1234|:8599|requests\.|"model"|MODEL\s*=|gemma|GEMMA|GROK|grok|shim|completions', l):
        print("  %4d: %s" % (i + 1, l.strip()[:104])); any3 = True
if not any3: print("  (none — module is pure logic, no LLM calls)")

print("\n======== (4) identity / pronoun occurrences (resolve direction by eye) ========")
for i, l in enumerate(L):
    if re.search(r'\bVelaris\b|\bshe\b|\bher\b|\bhers\b|\bherself\b|\bhis\b|\bhim\b|\bhe\b|\bhimself\b', l):
        kind = "PROMPT/STR" if ('"' in l or "'" in l) and not l.strip().startswith("#") else ("COMMENT" if l.strip().startswith("#") or '"""' in l else "code")
        print("  %4d [%s]: %s" % (i + 1, kind, l.strip()[:98]))

print("\n======== (5) triple-quoted prompt blocks (identity that reaches an LLM) ========")
intrip = False; buf = []
for i, l in enumerate(L):
    q = l.count('"""') + l.count("'''")
    if not intrip and q >= 1:
        intrip = True; start = i; buf = [l]
        if q >= 2: intrip = False; print("  %d: %s" % (i + 1, l.strip()[:100])); buf = []
        continue
    if intrip:
        buf.append(l)
        if q >= 1:
            intrip = False
            if len(buf) > 1 and any(re.search(r'Velaris|\bshe\b|\bher\b|you are|tends to|predict', x, re.I) for x in buf):
                print("  block @ %d-%d:" % (start + 1, i + 1))
                for x in buf[:14]: print("      | %s" % x.strip()[:96])

print("\n(READ-ONLY. Nothing changed. Sizes the her->his causal_self_model port precisely.)")
