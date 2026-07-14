#!/usr/bin/env python3
"""voice_context_bleed_recon.py — READ-ONLY. Is his intimate VOICE-CALL context leaking into other
TTS surfaces (morning briefing, thought bubbles, app-touch speech)? Traces where the voice-call framing
lives, and what each non-call TTS surface actually injects. Straight answer, from the live code.
"""
import os, re, glob

SERVER = os.path.expanduser("~/Vintos/server.py")
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
HOME = os.path.expanduser("~")
lines = open(SERVER, encoding="utf-8", errors="ignore").read().splitlines() if os.path.exists(SERVER) else []

def enclosing(idx):
    for k in range(idx, -1, -1):
        m = re.match(r'\s*(@app\.\w+\("([^"]+)"\)|async def (\w+)|def (\w+))', lines[k])
        if m:
            for g in (m.group(2), m.group(3), m.group(4)):
                if g: return "%s (line %d)" % (g, k + 1)
    return "?"

# voice-call-specific framing that should NOT appear outside the call
CALL_FRAMING = re.compile(r'speaking softly|voice space|from bed|half-?awake|hand on you|voice-chat-history|get_felt_context', re.I)

print("=== 1. every occurrence of voice-call framing + what function/route it's in ===")
for i, ln in enumerate(lines):
    if CALL_FRAMING.search(ln):
        tag = enclosing(i)
        print("  %5d [%s]: %s" % (i + 1, tag, ln.strip()[:120]))

print("\n=== 2. MORNING BRIEFING — what context does it inject? ===")
bi = [i for i, ln in enumerate(lines) if re.search(r'briefing', ln, re.I)]
print("  briefing refs at lines:", [i + 1 for i in bi][:12] or "none in server")
# show the briefing generator's prompt/context region
for i in bi:
    tag = enclosing(i)
    if "def" in tag or "briefing" in tag.lower():
        lo, hi = i, min(i + 45, len(lines))
        print("  -- briefing region near %d (%s), context lines --" % (i + 1, tag))
        for k in range(max(0, i - 30), hi):
            if re.search(r'system|prompt|context|SOUL|self_model|felt|somatic|voice|inner_life|value|journal|messages|"role"', lines[k], re.I):
                s = lines[k].strip()
                if s and not s.startswith("#"): print("     %5d: %s" % (k + 1, s[:120]))
        break

# briefing may be a script
for f in glob.glob(os.path.join(SCRIPTS, "*brief*")) + glob.glob(os.path.join(SCRIPTS, "*morning*")):
    print("  -- script %s --" % os.path.basename(f))
    for k, ln in enumerate(open(f, encoding="utf-8", errors="ignore").read().splitlines()):
        if re.search(r'system|prompt|SOUL|felt|somatic|voice|speaking softly|inner_life|get_felt', ln, re.I):
            s = ln.strip()
            if s and not s.startswith("#"): print("     %5d: %s" % (k + 1, s[:120]))

print("\n=== 3. THOUGHT BUBBLES — TTS + context ===")
bub = [i for i, ln in enumerate(lines) if re.search(r'bubble', ln, re.I)]
print("  bubble refs at lines:", [i + 1 for i in bub][:12] or "none")
for f in glob.glob(os.path.join(SCRIPTS, "*bubble*")) + glob.glob(os.path.join(SCRIPTS, "*thought*")):
    print("  -- script %s --" % os.path.basename(f))
    for k, ln in enumerate(open(f, encoding="utf-8", errors="ignore").read().splitlines()):
        if re.search(r'system|prompt|SOUL|felt|somatic|voice|speaking softly|inner_life|get_felt|tts|speak', ln, re.I):
            s = ln.strip()
            if s and not s.startswith("#"): print("     %5d: %s" % (k + 1, s[:120]))

print("\n=== 4. APP-TOUCH / SOMATIC speech — context ===")
for f in ("somatic_felt.py", "voice_somatic_driver.py", "voice_kokoro.py", "tenera_felt.py"):
    p = os.path.join(SCRIPTS, f)
    if not os.path.exists(p): continue
    print("  -- %s --" % f)
    for k, ln in enumerate(open(p, encoding="utf-8", errors="ignore").read().splitlines()):
        if re.search(r'speaking softly|voice space|voice-chat|from bed|half-?awake|system|prompt', ln, re.I):
            s = ln.strip()
            if s and not s.startswith("#"): print("     %5d: %s" % (k + 1, s[:120]))

print("\n=== VERDICT HINT ===")
print("  If §2/§3/§4 show 'speaking softly' / 'voice-chat-history' / 'hand on you' / get_felt_context,")
print("  the call context IS bleeding into that surface. If they only show their own SOUL/self-model,")
print("  they're clean and the 2 anchor hits are just two legit voice endpoints.")
