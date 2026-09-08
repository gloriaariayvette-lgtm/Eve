#!/usr/bin/env python3
"""voice_app_recon.py — READ-ONLY, flood-safe. Settle it from the app code: during a voice call, does
the client (a) POST /api/voice/chat and play the server's returned audio_url (= Kokoro), or (b) open its
own connection to xAI (api.x.ai / v1/tts / voice-agent / wss) = direct xAI? Prints only short windows
around each marker (handles minified bundles without flooding). Fresh name.
"""
import os, re, glob

HOME = os.path.expanduser("~")
SKIP = ("/node_modules/", "/.git/", "/.venv/", "/site-packages/", "-backup", "/__pycache__/")

# locate the frontend
APP_FILES = []
for pat in ("**/avatar-bundle.js", "**/index.html", "**/*.jsx", "**/*.tsx", "**/*.ts",
            "**/app*.js", "**/main*.js", "**/voice*.js", "**/voice*.ts"):
    for root in (os.path.join(HOME, "Vintos"), os.path.join(HOME, "vintos-app"),
                 os.path.join(HOME, "vintos-frontend"), os.path.join(HOME, ".vintos")):
        if os.path.isdir(root):
            APP_FILES += glob.glob(os.path.join(root, pat), recursive=True)
APP_FILES = sorted({f for f in APP_FILES if not any(s in f for s in SKIP) and os.path.isfile(f)})

DIRECT = re.compile(r'api\.x\.ai|//x\.ai|/v1/tts|/v1/voice|voice[-_]?agent|wss://[^"\']*x\.ai|agent_id|signed[_-]?url|voice_id|xi-api', re.I)
SERVER = re.compile(r'/api/voice/chat|/api/voice/transcribe|/api/voice/stream|audio_url|new Audio|<audio|MediaRecorder', re.I)

def windows(text, rx, w=55, cap=10):
    out, seen = [], 0
    for m in rx.finditer(text):
        s = max(0, m.start() - w); e = min(len(text), m.end() + w)
        snip = text[s:e].replace("\n", " ")
        snip = re.sub(r"\s+", " ", snip).strip()
        if snip not in out:
            out.append(snip); seen += 1
        if seen >= cap: break
    return out

print("=== frontend files found ===")
for f in APP_FILES[:20]:
    print("  %s (%d KB)" % (f.replace(HOME, "~"), os.path.getsize(f) // 1024))
if not APP_FILES:
    print("  none found in ~/Vintos, ~/vintos-app, ~/vintos-frontend, ~/.vintos")

print("\n=== per file: DIRECT-xAI markers vs SERVER-path markers ===")
for f in APP_FILES:
    try: t = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    d = windows(t, DIRECT); s = windows(t, SERVER)
    if not (d or s): continue
    print("\n  %s" % f.replace(HOME, "~"))
    if d:
        print("    DIRECT-xAI:")
        for w in d: print("      … %s …" % w[:120])
    if s:
        print("    SERVER-path:")
        for w in s: print("      … %s …" % w[:120])

# how does the server mount the app (where the live frontend actually is)?
print("\n=== where the server serves the app from ===")
srv = os.path.join(HOME, "Vintos", "server.py")
if os.path.exists(srv):
    for i, ln in enumerate(open(srv, encoding="utf-8", errors="ignore").read().splitlines()):
        if re.search(r'StaticFiles|mount\(|FileResponse\(.*html|directory=', ln):
            print("  %5d: %s" % (i + 1, ln.strip()[:130]))

print("\n=== READ ===")
print("  DIRECT-xAI markers in the app  -> calls go straight to xAI (server /api/voice/chat is a fallback)")
print("  only SERVER-path markers       -> app plays the server's Kokoro audio (xAI never reaches calls)")
