#!/usr/bin/env python3
"""voice_path_recon.py — READ-ONLY, bounded. Vintos's VOICE-CALL path only. Answers: which TTS
synthesizes his voice calls, does it accept expressive tags, and where does the somatic driver feed in
— so the emotion-vector->tag prosody injects at the right point. Fresh name.
"""
import os, re, glob

HIS_SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
HIS_SERVER  = os.path.expanduser("~/Vintos/server.py")
HOME = os.path.expanduser("~")

TTS = re.compile(
    r'kokoro|eleven|xi-api|elevenlabs|tts|synthes|\bspeak\b|ssml|voice_id|audio|\.wav|\.mp3|speech'
    r'|cartesia|openai.*audio|api\.|endpoint|POST|requests\.post|urllib|def ', re.I)
SOMA = re.compile(r'somatic|emotion|socket|prosody|felt|tag|\[pause\]|whisper|sigh|driver|vector', re.I)

def dump(path, rx, cap=22, label=""):
    if not os.path.exists(path):
        print("  (%s not found)" % path.replace(HOME, "~")); return
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    out = 0
    for i, ln in enumerate(lines):
        if rx.search(ln):
            s = ln.strip()
            if s and not s.startswith("#"):
                print("  %5d: %s" % (i + 1, s[:150])); out += 1
            if out >= cap:
                print("  ...(capped)"); break
    if not out: print("  (no matches)")

print("=== 1. his server: the voice-call handler + how it makes audio ===")
if os.path.exists(HIS_SERVER):
    lines = open(HIS_SERVER, encoding="utf-8", errors="ignore").read().splitlines()
    # find voice endpoints/handlers
    vh = [i for i, ln in enumerate(lines) if re.search(r'def voice_chat|/api/voice|voice_call|@app\.(post|websocket).*voice|def .*voice', ln, re.I)]
    print("  voice handlers at lines:", [i + 1 for i in vh][:10] or "none by that name")
    # show TTS-related lines across the server
    print("  -- TTS / audio synthesis lines in server --")
    out = 0
    for i, ln in enumerate(lines):
        if re.search(r'kokoro|eleven|xi-api|elevenlabs|synthes|voice_id|ssml|\.wav|\.mp3|tts|cartesia|speech', ln, re.I):
            s = ln.strip()
            if s and not s.startswith("#"):
                print("  %5d: %s" % (i + 1, s[:150])); out += 1
            if out >= 24: print("  ...(capped)"); break
    if not out: print("  (no TTS lines in server — synthesis likely in a script)")
else:
    print("  server not found")

print("\n=== 2. voice_kokoro.py — is Kokoro the TTS? does it take tags? ===")
dump(os.path.join(HIS_SCRIPTS, "voice_kokoro.py"), TTS)

print("\n=== 3. voice_somatic_driver.py — how the somatic already feeds voice ===")
dump(os.path.join(HIS_SCRIPTS, "voice_somatic_driver.py"), SOMA)

print("\n=== 4. voice_somatic_loop.py + somatic_felt.py — signals available ===")
for f in ("voice_somatic_loop.py", "somatic_felt.py"):
    print("  -- %s --" % f)
    dump(os.path.join(HIS_SCRIPTS, f), SOMA, cap=12)

print("\n=== 5. any elevenlabs/hosted-builder creds or config on his box? ===")
hits = []
for f in glob.glob(os.path.join(HIS_SCRIPTS, "*.py")) + [HIS_SERVER]:
    try: t = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if re.search(r'elevenlabs|xi-api|eleven_labs|ELEVEN|voice_agent|agent_id', t, re.I):
        hits.append(os.path.basename(f))
print("  files referencing a hosted voice builder:", sorted(set(hits)) or "NONE (likely local Kokoro)")
print("\n=== done ===")
