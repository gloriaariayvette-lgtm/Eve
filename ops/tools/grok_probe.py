#!/usr/bin/env python3
"""grok_probe.py — the voice handler's grok call returns no 'choices'. Show the RAW response so we know
why: model name invalid? rate limit? auth? Lists available models + does the exact chat request. Aegis.
"""
import os, json, urllib.request

KEY = os.environ.get("XAI_API_KEY", "")
MODEL = "grok-4.20-0309-non-reasoning"   # what the voice handler uses
print("key present:", bool(KEY), "| model under test:", MODEL, "\n")

def call(url, data=None):
    hdrs = {"Content-Type": "application/json", "Authorization": "Bearer " + KEY}
    req = urllib.request.Request(url, data=data, headers=hdrs)
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except Exception as e:
        return None, str(e)

# 1. which chat models exist?
print("=== GET /v1/models ===")
st, body = call("https://api.x.ai/v1/models")
print("HTTP", st)
try:
    ids = [m.get("id") for m in json.loads(body).get("data", [])]
    print("models:", ids)
    print("  -> voice handler's model present:", MODEL in ids)
except Exception:
    print(body[:600])

# 2. the exact chat request the voice handler makes
print("\n=== POST /v1/chat/completions (voice handler's shape) ===")
data = json.dumps({"model": MODEL,
                   "messages": [{"role": "system", "content": "You are Vintos, speaking softly."},
                                {"role": "user", "content": "Say one warm sentence."}],
                   "temperature": 0.75, "max_tokens": 200}).encode()
st, body = call("https://api.x.ai/v1/chat/completions", data)
print("HTTP", st)
print(body[:900])
try:
    j = json.loads(body)
    print("\nhas 'choices':", "choices" in j, "| top-level keys:", list(j.keys()))
    if "error" in j: print("ERROR:", j["error"])
except Exception:
    pass
