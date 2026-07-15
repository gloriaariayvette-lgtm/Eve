#!/usr/bin/env python3
"""recon_velaris_ce.py — Aegis, READ-ONLY, capped. Vintos has NO creative-expression.sh; must port
Velaris's music path faithfully. Show: (1) how Velaris gathers context (TEMPORAL/EMOTIONS/CREATIVE_CONTEXT
/taste) + which LLM endpoint it calls, (2) the music-prompt case + how the output is WRITTEN (OUTDIR /
filename format), (3) how dream-music.py CONSUMES that music-prompts dir — so the port produces exactly
what dream-music.py expects."""
import os, re
HOME = os.path.expanduser("~")
CE = os.path.join(HOME, ".openclaw/workspace/scripts/creative-expression.sh")
DM = os.path.join(HOME, ".openclaw/workspace/scripts/dream-music.py")
def sh(p): return p.replace(HOME, "~")

def show(path, pats, cap=40):
    if not os.path.isfile(path):
        print("  (missing)", sh(path)); return
    lines = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"  -- {sh(path)} ({len(lines)} lines) --")
    n = 0
    for i, l in enumerate(lines):
        if re.search(pats, l, re.I) and l.strip():
            print(f"   {i+1:4}| {l.strip()[:140]}"); n += 1
            if n >= cap: break

print("=== (1) Velaris creative-expression.sh: context vars + LLM endpoint/model + arg handling ===")
show(CE, r'TEMPORAL=|EMOTIONS=|CREATIVE_CONTEXT=|_CRE_|taste|MODE=|case |\$1|172\.18|api\.x\.ai|/v1/chat|model|MODEL=|SYSTEM_PROMPT=|curl|requests\.post|python3 -c', 32)

print("\n=== (2) how the music prompt OUTPUT is written (OUTDIR / filename / what gets saved) ===")
show(CE, r'OUTDIR|music-prompts|mkdir|> *"?\$|tee |cat >|OUTFILE|FNAME|date +|\.txt|\.md|save|write', 26)

print("\n=== (3) dream-music.py: how it CONSUMES the music-prompts dir (format it expects) ===")
show(DM, r'PROMPTS|music-prompts|listdir|glob|for .* in |open\(|read\(\)|TITLE|STYLE|parse|split|\.txt|\.md|MUSIC_WANT|def ', 34)
