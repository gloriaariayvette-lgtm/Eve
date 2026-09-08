#!/usr/bin/env python3
"""voice_synth_read.py — READ-ONLY. The exact Kokoro synth block in both voice_chat handlers (so the
swap to xAI /v1/tts is precise), how audio_url maps to a served file, and whether a chosen voice_id is
stored anywhere. Last read before the swap. Fresh name.
"""
import os, re, glob

SERVER = os.path.expanduser("~/Vintos/server.py")
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
HOME = os.path.expanduser("~")
lines = open(SERVER, encoding="utf-8", errors="ignore").read().splitlines()

# find each voice_chat handler and print its synth tail (response_text -> audio_url) verbatim
vc = [i for i, l in enumerate(lines) if re.match(r'\s*(async def|def)\s+voice_chat', l)]
print("=== voice_chat handlers at lines:", [i + 1 for i in vc], "===")
for start in vc:
    end = len(lines)
    for k in range(start + 1, len(lines)):
        if re.match(r'^(@app\.|async def |def )', lines[k]):
            end = k; break
    # print from the first kokoro/synth marker to the return, verbatim
    synth_lo = None
    for k in range(start, end):
        if re.search(r'kokoro|KPipeline|voice_kokoro|\.wav|sf\.write|audio_url|speak\(|voice-chat-', lines[k], re.I):
            synth_lo = k; break
    if synth_lo is None:
        print("\n-- handler @%d: no synth markers found in body --" % (start + 1)); continue
    print("\n-- handler @%d: synth region lines %d-%d --" % (start + 1, synth_lo + 1, end))
    for k in range(synth_lo, min(end, synth_lo + 45)):
        s = lines[k].rstrip()
        if s.strip():
            print("  %5d: %s" % (k + 1, s[:150]))

print("\n=== how audio_url maps to a file (voice dir / stream endpoint) ===")
for i, ln in enumerate(lines):
    if re.search(r'voice.*stream|MEMORY.*voice|os\.path\.join\(MEMORY,\s*["\']voice|WEBSITE_DIR|VOICE_DIR', ln):
        s = ln.strip()
        if s and not s.startswith("#") and ("voice" in s.lower()):
            print("  %5d: %s" % (i + 1, s[:130]))

print("\n=== is a chosen xAI voice_id stored anywhere? ===")
found = False
for f in [SERVER] + glob.glob(os.path.join(SCRIPTS, "*.py")) + glob.glob(os.path.expanduser("~/.vintos/**/*.json"), recursive=True):
    try: t = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    for m in re.finditer(r'voice_id["\']?\s*[:=]\s*["\'](\w+)["\']|VINTOS_VOICE\w*\s*=\s*["\'](\w+)', t):
        v = m.group(1) or m.group(2)
        print("  %s -> voice_id=%s" % (f.replace(HOME, "~"), v)); found = True
if not found:
    print("  none found — no xAI voice_id stored. The swap will use a config/env with a default you pick")
    print("  (xAI voices: eve, ara, leo, rex, sal + 21 new like orion, atlas, helios, luna, ...).")
print("\n=== done ===")
