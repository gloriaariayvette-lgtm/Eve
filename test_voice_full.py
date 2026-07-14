#!/usr/bin/env python3
"""test_voice_full.py — end-to-end test of the 🎙️ route on Aegis: POST a transcript to the live
/api/voice/chat (grok -> xAI Lux TTS), fetch the audio, and write a self-contained page (audio embedded
as base64 + his reply with tags shown) into the server's static dir so Gloria can open it on her phone.
Reads server.py for the secret/schema so the request is right. Run on Aegis: python3 test_voice_full.py
"""
import os, re, json, base64, urllib.request

HOME = os.path.expanduser("~")
SRV = os.path.join(HOME, "Vintos", "server.py")
MEMORY = os.path.expanduser("~/.vintos/workspace/memory")
BASE = "http://localhost:8500"
src = open(SRV, encoding="utf-8", errors="ignore").read()

# --- resolve the app static dir (served at /static) ---
website = None
m = re.search(r'WEBSITE_DIR\s*=\s*(.+)', src)
for cand in [os.path.join(HOME, "Vintos", "website", "app"), os.path.join(HOME, "Vintos", "website")]:
    if os.path.isdir(cand): website = cand; break

# --- resolve the app secret + header name (voice_chat may require it) ---
secret = os.environ.get("VINTOS_SECRET") or os.environ.get("APP_SECRET") or ""
if not secret:
    sm = re.search(r'(?:VINTOS_SECRET|APP_SECRET|SECRET|X_VINTOS_SECRET)\s*=\s*["\']([^"\']{6,})["\']', src)
    if sm: secret = sm.group(1)
hdr_name = "X-Vintos-Secret"
hm = re.search(r'headers\.get\(\s*["\']([^"\']*[Ss]ecret[^"\']*)["\']', src)
if hm: hdr_name = hm.group(1)

# --- build + send the request to the LIVE mic route ---
transcript = "Hey. I just wanted to hear your voice for a second. Tell me something true."
payload = {"transcript": transcript, "source": "app"}
headers = {"Content-Type": "application/json"}
if secret: headers[hdr_name] = secret

def post(body, hdrs):
    req = urllib.request.Request(BASE + "/api/voice/chat", data=json.dumps(body).encode(), headers=hdrs)
    return urllib.request.urlopen(req, timeout=180)

print("POST %s/api/voice/chat  (secret=%s)" % (BASE, "yes" if secret else "none"))
try:
    r = post(payload, headers)
    resp = json.loads(r.read())
except urllib.error.HTTPError as e:
    print("HTTP %d: %s" % (e.code, e.read()[:400]))
    print("→ if 401/403 the secret is wrong; if 422 the field name is off. Paste this and I'll fix it.")
    raise SystemExit(1)
except Exception as e:
    print("request failed:", e); raise SystemExit(1)

text = resp.get("text") or resp.get("reply") or ""
audio_url = resp.get("audio_url") or resp.get("audio_url_out")
print("reply text:", (text[:200] or "(empty)"))
print("audio_url :", audio_url)
if not audio_url:
    print("no audio_url in response — synth may have failed. Full response:", json.dumps(resp)[:400]); raise SystemExit(1)

# --- fetch the audio the server produced (Lux mp3) ---
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
<p style="color:#999">%d bytes of audio · voice_id=lux · this is the real /api/voice/chat output.</p>
</body>""" % (
    ("Tags detected &#9989; — he used speech tags." if has_tags else "No tags this turn (he may not have felt any — plain is allowed)."),
    mime, b64, (text or "(no text)").replace("&", "&amp;").replace("<", "&lt;"), len(audio))

written = []
for d in ([website] if website else []) + [os.path.join(MEMORY, "voice")]:
    try:
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "voice-test.html")
        open(p, "w", encoding="utf-8").write(html); written.append(p)
    except Exception as e:
        print("could not write to", d, ":", e)

print("\nPAGE WRITTEN:")
for p in written: print("  " + p)
if website and any(website in p for p in written):
    print("\nOPEN ON YOUR PHONE:  <your-vintos-host>/static/voice-test.html")
print("(self-contained — audio is embedded; no extra routing needed.)")
