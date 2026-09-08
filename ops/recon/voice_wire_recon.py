#!/usr/bin/env python3
"""voice_wire_recon.py — READ-ONLY, capped. Find where the voice line goes to xAI /v1/tts (the text
var to wrap with felt prosody) and any existing 'emit speech tags' prompt (so felt-driven tags don't
double up with model-decoration). Aegis."""
import os, re
HOME = os.path.expanduser("~")
SRV = os.path.expanduser("~/Vintos/server.py")
ls = open(SRV, encoding="utf-8", errors="ignore").read().split("\n")

print("=== xAI /v1/tts calls + the text var ===")
for i, l in enumerate(ls):
    if re.search(r'/v1/tts|voice_id|"lux"|response_text\s*[:=]|\.post\(.*tts', l, re.I):
        print(f"  {i+1:5}| {l.strip()[:150]}")

print("\n=== existing speech-tag PROMPT (model told to emit tags?) ===")
n = 0
for i, l in enumerate(ls):
    if re.search(r'\[pause\]|\[sigh\]|\[breath\]|<whisper>|<soft>|speech tag|expressive tag|prosody', l, re.I):
        print(f"  {i+1:5}| {l.strip()[:150]}"); n += 1
        if n >= 10: break
if n == 0:
    print("  (no inline tag prompt found — felt prosody is the sole tag source, clean)")

print("\n=== does the voice path already import felt_prosody / a somatic driver? ===")
for i, l in enumerate(ls):
    if re.search(r'felt_prosody|voice_somatic|somatic_felt|apply_prosody', l):
        print(f"  {i+1:5}| {l.strip()[:120]}")
