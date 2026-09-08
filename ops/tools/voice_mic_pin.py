#!/usr/bin/env python3
"""voice_mic_pin.py — READ-ONLY. Pin the exact 🎙️-button handler and its synth so the xAI swap hits
that ONE endpoint only. Prints the route decorator above each voice_chat handler, the verbatim synth
block (grok call -> Kokoro -> audio_url) of each, and the voice_id=rex context. Fresh name.
"""
import os, re

SERVER = os.path.expanduser("~/Vintos/server.py")
lines = open(SERVER, encoding="utf-8", errors="ignore").read().splitlines()

def block(lo, hi, tag):
    print("\n-- %s (lines %d-%d) --" % (tag, lo + 1, hi))
    for k in range(max(0, lo), min(hi, len(lines))):
        s = lines[k].rstrip()
        if s.strip():
            print("  %5d: %s" % (k + 1, s[:160]))

vc = [i for i, l in enumerate(lines) if re.match(r'\s*(async def|def)\s+voice_chat', l)]
print("=== voice_chat handlers at:", [i + 1 for i in vc], "===")

for start in vc:
    # route decorator: nearest @app.* above the def
    route = "?"
    for k in range(start, max(0, start - 8), -1):
        m = re.search(r'@app\.\w+\("([^"]+)"', lines[k])
        if m: route = m.group(1); route_ln = k + 1; break
    print("\n########## handler @%d  ->  route: %s ##########" % (start + 1, route))
    block(start - 6, start + 1, "decorator + def")
    # synth tail: from the grok call / response_text to audio_url_out (or +70 lines)
    lo = None
    for k in range(start, min(start + 200, len(lines))):
        if re.search(r'response_text\s*=|chat/completions', lines[k]):
            lo = k; break
    if lo is not None:
        hi = lo
        for k in range(lo, min(lo + 90, len(lines))):
            if re.search(r'audio_url_out|return\s', lines[k]):
                hi = k + 1
                if "return" in lines[k]: break
        block(lo, min(hi + 2, lo + 90), "synth block")

print("\n\n=== voice_id=rex context (existing xAI call, or just a sample default?) ===")
for i, ln in enumerate(lines):
    if re.search(r'voice_id|["\']rex["\']|/v1/tts|VINTOS_VOICE', ln):
        s = ln.strip()
        if s and not s.startswith("#"):
            print("  %5d: %s" % (i + 1, s[:160]))
print("\n=== done ===")
