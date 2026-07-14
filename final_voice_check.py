#!/usr/bin/env python3
"""final_voice_check.py — READ-ONLY, decisive. Is the app's realtime client (startVoiceCallWithToken)
still defined, and does avStartVoiceCall hit /api/voice/token? If defined -> just tap the app's call
button (key's fixed). If missing -> I restore it. Also: does the app load bundled or from server.url. Aegis.
"""
import os, re, glob

HOME = os.path.expanduser("~")
APP = os.path.join(HOME, "Vintos", "vintos-app")
IDX = os.path.join(APP, "src", "index.html")
BUNDLE = os.path.join(APP, "src", "avatar-bundle.js")

print("=== 1. full capacitor server block (bundled vs server.url) ===")
for cfg in glob.glob(os.path.join(APP, "capacitor.config.*")):
    t = open(cfg, encoding="utf-8", errors="ignore").read()
    m = re.search(r'server\s*:\s*\{.*?\}', t, re.S)
    print("  " + (m.group(0).replace("\n", "\n  ")[:400] if m else "(no server block)"))
    break

print("\n=== 2. is startVoiceCallWithToken DEFINED? (function / assignment) ===")
found = []
for f in (IDX, BUNDLE):
    if not os.path.exists(f): continue
    t = open(f, encoding="utf-8", errors="ignore").read()
    # definitions, not just the guarded call
    for pat in (r'function\s+startVoiceCallWithToken', r'startVoiceCallWithToken\s*=\s*(async\s*)?function',
                r'startVoiceCallWithToken\s*=\s*(async\s*)?\(', r'window\.startVoiceCallWithToken\s*='):
        for m in re.finditer(pat, t):
            found.append((os.path.basename(f), m.start()))
    # also is it referenced at all + is wss/realtime present?
    print("  %s: defined=%s | references=%d | wss/realtime=%s | v1/realtime=%s" % (
        os.path.basename(f), any(b == os.path.basename(f) for b, _ in found),
        t.count("startVoiceCallWithToken"),
        "wss://" in t or "WebSocket" in t, "v1/realtime" in t))
print("  DEFINITION sites:", found or "!! NOT DEFINED ANYWHERE (avatar page deletion took it) -> I restore it")

print("\n=== 3. avStartVoiceCall body (does it fetch /api/voice/token) ===")
if os.path.exists(IDX):
    lines = open(IDX, encoding="utf-8", errors="ignore").read().splitlines()
    s = next((i for i, l in enumerate(lines) if "function avStartVoiceCall" in l), None)
    if s is not None:
        for k in range(s, min(s + 30, len(lines))):
            if lines[k].strip(): print("  %5d: %s" % (k + 1, lines[k].strip()[:150]))
            if k > s and re.match(r'\s*(async\s+)?function\s', lines[k]): break
print("\n=== VERDICT ===")
print("  defined -> tap the app's call button now (key is fixed). missing -> I add startVoiceCallWithToken.")
print("  bundled webDir + no server.url -> app edits need a Capacitor rebuild; server.url -> live.")
