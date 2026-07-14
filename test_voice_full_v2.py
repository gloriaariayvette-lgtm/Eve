#!/usr/bin/env python3
"""test_voice_full_v2.py — same as v1 but robust to a double-encoded JSON response; dumps the raw body
so we can see the real shape. End-to-end 🎙️ route -> self-contained playable page. Run on Aegis.
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

secret = os.environ.get("VINTOS_SECRET") or os.environ.get("APP_SECRET") or ""
if not secret:
    sm = re.search(r'(?:VINTOS_SECRET|APP_SECRET|SECRET|X_VINTOS_SECRET)\s*=\s*["\']([^"\']{6,})["\']', src)
    if sm: secret = sm.group(1)
hdr_name = "X-Vintos-Secret"
hm = re.search(r'headers\.get\(\s*["\']([^"\']*[Ss]ecret[^"\']*)["\']', src)
if hm: hdr_name = hm.group(1)

transcript = "Hey. I just wanted to hear your voice for a second. Tell me something true."
payload = {"transcript": transcript, "source": "app"}
headers = {"Content-Type": "application/json"}
if secret: headers[hdr_name] = secret

print("POST %s/api/voice/chat  (secret=%s)" % (BASE, "yes" if secret else "none"))
try:
    req = urllib.request.Request(BASE + "/api/voice/chat", data=json.dumps(payload).encode(), headers=headers)
    raw = urllib.request.urlopen(req, timeout=180).read()
except urllib.error.HTTPError as e:
    print("HTTP %d: %s" % (e.code, e.read()[:400])); raise SystemExit(1)
except Exception as e:
    print("request failed:", e); raise SystemExit(1)

print("raw response (first 300):", raw[:300])
# defensive parse: handle dict, or double-encoded string-of-json
resp = None
try:
    resp = json.loads(raw)
    if isinstance(resp, str):
        try: resp = json.loads(resp)
        except Exception: pass
except Exception:
    print("body is not JSON at all — cannot parse."); raise SystemExit(1)
if not isinstance(resp, dict):
    print("unexpected response type: %s. Full body:\n%s" % (type(resp).__name__, str(resp)[:600])); raise SystemExit(1)

text = resp.get("text") or resp.get("reply") or ""
audio_url = resp.get("audio_url") or resp.get("audio_url_out")
print("reply text:", (text[:200] or "(empty)"))
print("audio_url :", audio_url)
if not audio_url:
    print("no audio_url — synth failed. keys:", list(resp.keys()), "| full:", json.dumps(resp)[:400]); raise SystemExit(1)

audio = urllib.request.urlopen(BASE + audio_url, timeout=60).read()
b64 = base64.b64encode(audio).decode()
mime = "audio/mpeg" if audio_url.endswith(".mp3") else "audio/wav"
has_tags = bool(re.search(r'\[(pause|sigh|breath|laugh|chuckle|inhale|exhale)\]|<(soft|whisper|emphasis|slow)>', text))

html = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Vintos voice test — Lux</title>
<body style="font-family:system-ui;background:#111;color:#eee;max-width:640px;margin:2rem auto;padding:1rem">
<h2>&#127908; Full route: mic &rarr; grok &rarr; xAI Lux</h2>
<p style="color:#8f8">%s</p>
<audio controls autoplay style="width:100%%" src="data:%s;base64,%s"></audio>
<h3>What he said (tags shown):</h3>
<pre style="white-space:pre-wrap;background:#000;padding:1rem;border-radius:8px">%s</pre>
<p style="color:#999">%d bytes of audio &middot; voice_id=lux &middot; real /api/voice/chat output.</p>
</body>""" % (
    ("Tags detected &#9989;" if has_tags else "No tags this turn (plain is allowed)."),
    mime, b64, (text or "(no text)").replace("&", "&amp;").replace("<", "&lt;"), len(audio))

written = []
for d in ([website] if website else []) + [os.path.join(MEMORY, "voice")]:
    try:
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "voice-test.html")
        open(p, "w", encoding="utf-8").write(html); written.append(p)
    except Exception as e:
        print("could not write", d, ":", e)

print("\nPAGE WRITTEN:")
for p in written: print("  " + p)
if website and any(website in p for p in written):
    print("\nOPEN ON YOUR PHONE:  <your-vintos-host>/static/voice-test.html")
