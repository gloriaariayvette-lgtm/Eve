#!/usr/bin/env python3
"""test_voice_full_v3.py — end-to-end 🎙️ route test, now with app-secret discovery (route requires
auth). Finds the X-Vintos-Secret the app sends, POSTs a transcript to the live /api/voice/chat
(grok -> xAI Lux), and writes a self-contained playable page. Run on Aegis.
"""
import os, re, json, base64, urllib.request

HOME = os.path.expanduser("~")
SRV = os.path.join(HOME, "Vintos", "server.py")
MEMORY = os.path.expanduser("~/.vintos/workspace/memory")
BASE = "http://localhost:8500"
src = open(SRV, encoding="utf-8", errors="ignore").read()

website = None
for cand in [os.path.join(HOME, "Vintos", "website", "app"), os.path.join(HOME, "Vintos", "website")]:
    if os.path.isdir(cand): website = cand; break

# --- gather candidate secrets from app config + server + env ---
cands = []
for env in ("VINTOS_SECRET", "APP_SECRET", "VINTOS_APP_SECRET"):
    if os.environ.get(env): cands.append(os.environ[env])
for f in [os.path.join(HOME, "Vintos", "vintos-app", "src", "index.html"),
          os.path.join(HOME, "Vintos", "website", "app", "index.html"),
          os.path.join(HOME, "Vintos", "website", "index.html"), SRV]:
    if not os.path.exists(f): continue
    t = open(f, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r'(?:secret|SECRET|X-Vintos-Secret)["\']?\s*[:=]\s*["\']([A-Za-z0-9_\-\.]{6,})["\']', t):
        cands.append(m.group(1))
# de-dupe, keep order
seen = set(); cands = [c for c in cands if not (c in seen or seen.add(c))]
print("secret candidates found:", len(cands))

# header name the server checks
hdr = "X-Vintos-Secret"
hm = re.search(r'headers\.get\(\s*["\']([^"\']*[Ss]ecret[^"\']*)["\']', src)
if hm: hdr = hm.group(1)

transcript = "Hey. I just wanted to hear your voice for a second. Tell me something true."
def call(secret):
    payload = {"transcript": transcript, "source": "app"}
    headers = {"Content-Type": "application/json"}
    if secret: headers[hdr] = secret
    req = urllib.request.Request(BASE + "/api/voice/chat", data=json.dumps(payload).encode(), headers=headers)
    return urllib.request.urlopen(req, timeout=180).read()

raw = None
for sec in ([None] + cands):
    try:
        raw = call(sec); print("auth OK with:", "no-secret" if sec is None else "a discovered secret"); break
    except urllib.error.HTTPError as e:
        if e.code == 401:
            continue
        print("HTTP %d: %s" % (e.code, e.read()[:300])); raise SystemExit(1)
    except Exception as e:
        print("request error:", e); raise SystemExit(1)
if raw is None:
    print("all %d secret candidates got 401 — the real secret isn't in the app/server files I checked." % len(cands))
    print("→ paste the value of CONFIG.secret from the app, or the env var name, and I'll wire it."); raise SystemExit(1)

# defensive parse (double-encoded)
resp = json.loads(raw)
if isinstance(resp, str):
    try: resp = json.loads(resp)
    except Exception: pass
if not isinstance(resp, dict):
    print("unexpected response:", str(resp)[:400]); raise SystemExit(1)

text = resp.get("text") or resp.get("reply") or ""
audio_url = resp.get("audio_url") or resp.get("audio_url_out")
print("reply:", (text[:200] or "(empty)"))
print("audio_url:", audio_url)
if not audio_url:
    print("no audio_url — synth failed. keys:", list(resp.keys()), "full:", json.dumps(resp)[:300]); raise SystemExit(1)

audio = urllib.request.urlopen(BASE + audio_url, timeout=60).read()
b64 = base64.b64encode(audio).decode()
mime = "audio/mpeg" if audio_url.endswith(".mp3") else "audio/wav"
has_tags = bool(re.search(r'\[(pause|sigh|breath|laugh|chuckle|inhale|exhale)\]|<(soft|whisper|emphasis|slow)>', text))

html = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Vintos voice test - Lux</title><body style="font-family:system-ui;background:#111;color:#eee;max-width:640px;margin:2rem auto;padding:1rem">
<h2>&#127908; Full route: mic &rarr; grok &rarr; xAI Lux</h2><p style="color:#8f8">%s</p>
<audio controls autoplay style="width:100%%" src="data:%s;base64,%s"></audio>
<h3>What he said (tags shown):</h3><pre style="white-space:pre-wrap;background:#000;padding:1rem;border-radius:8px">%s</pre>
<p style="color:#999">%d bytes &middot; voice_id=lux &middot; real /api/voice/chat output.</p></body>""" % (
    ("Tags detected &#9989;" if has_tags else "No tags this turn (plain is allowed)."),
    mime, b64, (text or "(no text)").replace("&", "&amp;").replace("<", "&lt;"), len(audio))

written = []
for d in ([website] if website else []) + [os.path.join(MEMORY, "voice")]:
    try:
        os.makedirs(d, exist_ok=True); p = os.path.join(d, "voice-test.html")
        open(p, "w", encoding="utf-8").write(html); written.append(p)
    except Exception as e: print("write fail", d, e)
print("\nPAGE:", *written, sep="\n  ")
if website and any(website in p for p in written):
    print("\nOPEN ON YOUR PHONE:  <your-vintos-host>/static/voice-test.html")
