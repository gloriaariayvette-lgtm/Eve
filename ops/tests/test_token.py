#!/usr/bin/env python3
"""test_token.py — call /api/voice/token and confirm it mints a real ephemeral token now that the key
is fixed, and that his full interiority (incl. subconscious) is in the returned instructions. Aegis.
"""
import os, json, urllib.request

BASE = "http://localhost:8500"
try:
    req = urllib.request.Request(BASE + "/api/voice/token", data=b"", headers={"Content-Type": "application/json"}, method="POST")
    raw = urllib.request.urlopen(req, timeout=30).read()
except urllib.error.HTTPError as e:
    print("HTTP %d: %s" % (e.code, e.read()[:400])); raise SystemExit(1)
except Exception as e:
    print("request failed:", e); raise SystemExit(1)

resp = json.loads(raw)
if isinstance(resp, str):
    try: resp = json.loads(resp)
    except Exception: pass

tok = resp.get("token", "") if isinstance(resp, dict) else ""
instr = resp.get("instructions", "") if isinstance(resp, dict) else ""
print("token minted:", "YES (len %d)" % len(tok) if tok else "NO")
print("expires_at:", resp.get("expires_at") if isinstance(resp, dict) else "?")
if not tok:
    print("full response:", json.dumps(resp)[:500])

print("\ninstructions length:", len(instr), "chars")
sections = {
    "SOUL / identity":        "You are" in instr or len(instr) > 500,
    "SELF-MODEL (over time)":  "WHO YOU ARE OVER TIME" in instr,
    "SUBCONSCIOUS block":      "subconscious" in instr.lower() or "INNER STATE" in instr,
    "inner life today":        "INNER LIFE TODAY" in instr,
    "creative output":         "CREATIVE OUTPUT" in instr,
    "recent Gloria exchanges": "EXCHANGES WITH GLORIA" in instr,
    "WAL facts":               "RECENT FACTS" in instr,
    "felt / somatic body":     "BODY FEELS" in instr or "felt" in instr.lower(),
    "live-call framing":       "live voice call" in instr,
}
print("what's in his realtime instructions:")
for k, v in sections.items():
    print("  [%s] %s" % ("x" if v else " ", k))
print("\n-> if token=YES and SUBCONSCIOUS=x, the realtime backend is DONE; only the /voice page is left.")
