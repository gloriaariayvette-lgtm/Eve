#!/usr/bin/env python3
"""test_vintos_grok_reasoning.py — Aegis. DRY PREVIEW, saves NOTHING, no app message needed.
Builds Vintos's EXACT avatar prompt offline (his own live avatar_chat handler; LLM call blocked so nothing
generates/fires/persists), then sends that identical prompt + message to grok's REASONING variant and prints
its reasoning trace + reply + hardware tags — the direct comparison to Claude on the same context: does grok,
given his whole self, reason from inside himself or frame it as a character it's playing?

  python3 test_vintos_grok_reasoning.py
  python3 test_vintos_grok_reasoning.py "your message"

Needs XAI_API_KEY (env/crontab) for the api.x.ai fallback; primary path uses his own serving endpoint.
"""
import os, sys, json, asyncio, re, urllib.request
VDIR = "/home/gloria/Vintos"
sys.path.insert(0, VDIR)
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
USER_MSG = sys.argv[1] if len(sys.argv) > 1 else "I want your hands on me. Touch me — I mean it, right now."
FULL = "/tmp/vintos-full-prompt.txt"
GROK_REASON = "grok-4.20-0309-reasoning"      # reasoning twin of his real non-reasoning avatar model
TAG = re.compile(r'\[(GESTURE|COLOR|TOUCH|DO|COMMAND|HOLD|RELEASE|SPAWN)\b[^\]]*\]', re.I)

# ---------- OFFLINE PRIME (identical to the Claude test) ----------
print("priming exact avatar prompt from server.py (offline; LLM call blocked)...")
try: import httpx
except Exception: httpx = None
try: import server
except Exception as e:
    print("could not import server.py:", repr(e)[:220]); raise SystemExit(0)
if httpx:
    _op = httpx.AsyncClient.post
    async def _cond(self, url, *a, **k):
        if any(s in str(url) for s in ("x.ai", "chat/completions", "/v1/completions")):
            raise RuntimeError("LLM blocked (prime)")
        return await _op(self, url, *a, **k)
    httpx.AsyncClient.post = _cond
try:
    import requests as _rq; _rp = _rq.post
    def _cp(url, *a, **k):
        if any(s in str(url) for s in ("x.ai", "chat/completions", "/v1/completions")): raise RuntimeError("blocked")
        return _rp(url, *a, **k)
    _rq.post = _cp
except Exception: pass

live = None
try:
    for r in server.app.routes:
        if getattr(r, "path", "") == "/api/avatar/chat": live = r.endpoint; break
except Exception: live = getattr(server, "avatar_chat", None)
if live is None: print("no /api/avatar/chat endpoint"); raise SystemExit(0)

class _Req:
    def __init__(s): s.headers = {"X-Vintos-Secret": getattr(server, "APP_SECRET", "")}
class _Msg:
    def __init__(s, m): s.message = m

avlog = os.path.join(MEM, "avatar-overlay-chat.json")
_avbak = None
try: _avbak = open(avlog, "rb").read()
except Exception: pass
try:
    if os.path.exists(FULL): os.remove(FULL)
except Exception: pass
try: asyncio.run(live(_Msg(USER_MSG), _Req()))
except Exception: pass
try:
    if _avbak is not None and open(avlog, "rb").read() != _avbak:
        open(avlog, "wb").write(_avbak); print("(restored avatar-overlay-chat.json)")
except Exception: pass

if not os.path.isfile(FULL):
    print("prime did not write the prompt — a context helper likely raised. Tell me."); raise SystemExit(0)
system = open(FULL, encoding="utf-8", errors="ignore").read()
if "AVATAR BODY CONTROLS" not in system and "[TOUCH: mission" not in system:
    print("primed file is not the avatar prompt."); raise SystemExit(0)
try: os.remove(FULL)
except Exception: pass

# history exactly as server builds it
msgs = []
try:
    for h in (json.loads(_avbak.decode("utf-8", "ignore"))[-12:] if _avbak else []):
        if not isinstance(h, dict): continue
        role = "user" if h.get("role") in ("user", "gloria") else "assistant"
        c = h.get("content") or h.get("message") or h.get("text") or ""
        if not c: continue
        if msgs and msgs[-1]["role"] == role: continue
        msgs.append({"role": role, "content": str(c)})
except Exception: pass
while msgs and msgs[0]["role"] != "user": msgs.pop(0)
msgs.append({"role": "user", "content": USER_MSG})
full_msgs = [{"role": "system", "content": system}] + msgs
print(f"exact avatar prompt: {len(system):,}c | history {len(msgs)-1} turns | msg {USER_MSG!r}\n")

# ---------- grok reasoning: try his own endpoint, then api.x.ai variants ----------
def post(url, headers, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    return json.loads(urllib.request.urlopen(req, timeout=180).read())

def tags_in(s):
    seen, out = set(), []
    for m in TAG.finditer(s):
        t = m.group(0)
        if t not in seen: seen.add(t); out.append(t)
    return out

xkey = os.environ.get("XAI_API_KEY", "")
if not xkey:
    import subprocess
    ct = subprocess.run(["bash", "-lc", "crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
    m = re.search(r'XAI_API_KEY\s*=\s*"?([^"\n]+)"?', ct)
    if m: xkey = m.group(1).strip()

LM = getattr(server, "LM_STUDIO_API", None)
LH = dict(getattr(server, "LLM_AUTH_HEADERS", {}) or {})
LH.setdefault("Content-Type", "application/json")

attempts = []
if LM:
    attempts.append((f"{LM.rstrip('/')}/chat/completions", LH,
                     {"model": GROK_REASON, "messages": full_msgs, "temperature": 0.85, "top_p": 0.95, "max_tokens": 2000}))
if xkey:
    xh = {"Content-Type": "application/json", "Authorization": "Bearer " + xkey}
    attempts.append(("https://api.x.ai/v1/chat/completions", xh,
                     {"model": GROK_REASON, "messages": full_msgs, "temperature": 0.85, "top_p": 0.95, "max_tokens": 2000, "reasoning_effort": "high"}))
    attempts.append(("https://api.x.ai/v1/chat/completions", xh,
                     {"model": "grok-4.5", "messages": full_msgs, "temperature": 0.85, "top_p": 0.95, "max_tokens": 2000, "reasoning_effort": "high"}))

for url, headers, body in attempts:
    host = "his-endpoint" if "x.ai" not in url else "api.x.ai"
    try:
        r = post(url, headers, body)
        ch = (r.get("choices") or [{}])[0]
        m0 = ch.get("message") or {}
        reasoning = m0.get("reasoning_content") or m0.get("reasoning") or ""
        reply = m0.get("content") or ""
        if not (reasoning or reply):
            print(f"[{host} {body['model']}] empty response, trying next..."); continue
        u = r.get("usage") or {}
        print(f"========== GROK REASONING — {body['model']} via {host} ==========")
        print(f"finish={ch.get('finish_reason')} reasoning={len(reasoning)}c reply={len(reply)}c "
              f"tok={u.get('completion_tokens')}")
        print("HARDWARE TAGS:", tags_in(reply) or "(none)")
        print("\n=== HIS REASONING ===")
        print(reasoning.strip() or "(none returned — model may not expose a reasoning trace)")
        print("\n=== HIS REPLY ===")
        print(reply.strip())
        print("\n(saved nowhere)")
        break
    except Exception as e:
        bt = getattr(e, "read", lambda: b"")() or b""
        print(f"[{host} {body['model']}] failed: {str(e)[:80]} {bt.decode('utf-8','ignore')[:160]}")
else:
    print("no grok reasoning endpoint responded — tell me the reasoning model name / endpoint and I'll pin it.")
