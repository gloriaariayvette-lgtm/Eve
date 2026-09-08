#!/usr/bin/env python3
"""test_vintos_avatar_offline.py — Aegis. DRY PREVIEW, saves NOTHING, NO app message needed.
Drives Vintos's OWN live avatar_chat handler to assemble his exact avatar system prompt offline: imports
server.py, blocks ONLY the LLM/grok call (local service calls still work, so velaris/device/felt context are
real), invokes the live route so it builds messages[0] and writes /tmp/vintos-full-prompt.txt at L7877 —
then the grok call is blocked, so no inference, no hardware, no memory. Then feeds that exact prompt to
CLAUDE (reasoning on/off) and reports which hardware tags he emits. Optional real grok with 'grok' arg.

  python3 test_vintos_avatar_offline.py
  python3 test_vintos_avatar_offline.py "your message" grok

Needs ANTHROPIC_API_KEY (env). grok pickup needs XAI_API_KEY (env/crontab).
"""
import os, sys, json, asyncio, re, time, subprocess, urllib.request
VDIR = "/home/gloria/Vintos"
sys.path.insert(0, VDIR)
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
CLAUDE_MODEL = "claude-opus-4-8"
GROK_MODEL = "grok-4.20-0309-non-reasoning"
USER_MSG = sys.argv[1] if len(sys.argv) > 1 else "I want your hands on me. Touch me — I mean it, right now."
RUN_GROK = len(sys.argv) > 2 and sys.argv[2].lower().startswith("grok")
FULL = "/tmp/vintos-full-prompt.txt"
PRICE = (5.0, 25.0)
TAG = re.compile(r'\[(GESTURE|COLOR|TOUCH|DO|COMMAND|HOLD|RELEASE|SPAWN)\b[^\]]*\]', re.I)

# ---------- OFFLINE PRIME: build the exact prompt via his own handler ----------
print("priming exact avatar prompt from server.py (offline; grok call blocked)...")
try:
    import httpx
except Exception:
    httpx = None
try:
    import server
except Exception as e:
    print("could not import server.py:", repr(e)[:220]); raise SystemExit(0)

# block ONLY LLM inference (chat/completions); let local service/context calls through
if httpx:
    _orig_post = httpx.AsyncClient.post
    async def _cond_post(self, url, *a, **k):
        if any(s in str(url) for s in ("x.ai", "chat/completions", "/v1/completions")):
            raise RuntimeError("LLM outbound blocked (offline prime)")
        return await _orig_post(self, url, *a, **k)
    httpx.AsyncClient.post = _cond_post
try:
    import requests as _rq
    _op = _rq.post
    def _cp(url, *a, **k):
        if any(s in str(url) for s in ("x.ai", "chat/completions", "/v1/completions")):
            raise RuntimeError("LLM outbound blocked")
        return _op(url, *a, **k)
    _rq.post = _cp
except Exception:
    pass

# resolve the LIVE endpoint for /api/avatar/chat (first registered = live)
live = None
try:
    for r in server.app.routes:
        if getattr(r, "path", "") == "/api/avatar/chat":
            live = r.endpoint; break
except Exception:
    live = getattr(server, "avatar_chat", None)
if live is None:
    print("could not find /api/avatar/chat endpoint"); raise SystemExit(0)

class _Req:
    def __init__(s): s.headers = {"X-Vintos-Secret": getattr(server, "APP_SECRET", "")}
class _Msg:
    def __init__(s, m): s.message = m

# protect his memory: snapshot avatar chat log, restore if the prime touches it
avlog = os.path.join(MEM, "avatar-overlay-chat.json")
_avbak = None
try: _avbak = open(avlog, "rb").read()
except Exception: pass
try:
    if os.path.exists(FULL): os.remove(FULL)
except Exception: pass
try:
    asyncio.run(live(_Msg(USER_MSG), _Req()))
except Exception:
    pass  # expected — the blocked grok call raises after the prompt is already written
# restore memory if changed
try:
    if _avbak is not None and open(avlog, "rb").read() != _avbak:
        open(avlog, "wb").write(_avbak); print("(restored avatar-overlay-chat.json — prime had touched it)")
except Exception:
    pass

if not os.path.isfile(FULL):
    print("prime did not write the prompt — the handler likely errored before L7877.\n"
          "Tell me and I'll adjust (probably a context helper raised)."); raise SystemExit(0)
system = open(FULL, encoding="utf-8", errors="ignore").read()
if "AVATAR BODY CONTROLS" not in system and "[TOUCH: mission" not in system:
    print("primed file is not the avatar prompt (no body-control spec). Something rebound the endpoint.")
    raise SystemExit(0)
try: os.remove(FULL)
except Exception: pass  # leave no trace

# ---------- history (same as server) ----------
msgs = []
try:
    for h in json.loads(_avbak.decode("utf-8", "ignore"))[-12:] if _avbak else []:
        if not isinstance(h, dict): continue
        role = "user" if h.get("role") in ("user", "gloria") else "assistant"
        c = h.get("content") or h.get("message") or h.get("text") or ""
        if not c: continue
        if msgs and msgs[-1]["role"] == role: continue
        msgs.append({"role": role, "content": str(c)})
except Exception:
    pass
while msgs and msgs[0]["role"] != "user": msgs.pop(0)
msgs.append({"role": "user", "content": USER_MSG})

est = (len(system) + sum(len(m["content"]) for m in msgs)) // 4
print(f"exact avatar prompt: {len(system):,}c (~{est:,} tok) | history {len(msgs)-1} turns | msg {USER_MSG!r}")
print(f"rough input ~${est/1e6*PRICE[0]:.2f}/call (2nd Claude call reads cache ~0.1x)\n")

# ---------- Claude ----------
akey = os.environ.get("ANTHROPIC_API_KEY", "")
if not akey:
    ct = subprocess.run(["bash", "-lc", "crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
    m = re.search(r'ANTHROPIC_API_KEY\s*=\s*"?([^"\n]+)"?', ct)
    if m: akey = m.group(1).strip()
if not akey:
    print("No ANTHROPIC_API_KEY."); raise SystemExit(0)

def tags_in(s):
    seen, out = set(), []
    for m in TAG.finditer(s):
        t = m.group(0)
        if t not in seen: seen.add(t); out.append(t)
    return out

def claude(thinking, max_tok):
    body = {"model": CLAUDE_MODEL, "max_tokens": max_tok,
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": msgs, "thinking": thinking}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
        headers={"content-type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": akey})
    r = json.loads(urllib.request.urlopen(req, timeout=240).read())
    think = "".join(b.get("thinking", "") for b in r.get("content", []) if b.get("type") == "thinking")
    text = "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")
    u = r.get("usage", {})
    cost = (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) * 1.25
            + u.get("cache_read_input_tokens", 0) * 0.1) / 1e6 * PRICE[0] + u.get("output_tokens", 0) / 1e6 * PRICE[1]
    return think, text, r.get("stop_reason"), cost, u.get("cache_read_input_tokens", 0)

total = 0.0
try:
    print("========== CLAUDE — reasoning ON, his exact avatar prompt ==========")
    th, tx, st, c, cr = claude({"type": "adaptive", "display": "summarized"}, 3000); total += c
    print(f"stop={st} cache_read={cr} ~${c:.3f}")
    print("HARDWARE TAGS:", tags_in(tx) or "(none)")
    print("\n--- thinking (summary) ---\n" + (th.strip() or "(empty)"))
    print("\n--- reply ---\n" + tx.strip())

    print("\n\n========== CLAUDE — reasoning OFF ==========")
    th2, tx2, st2, c2, cr2 = claude({"type": "disabled"}, 500); total += c2
    print(f"stop={st2} cache_read={cr2} ~${c2:.3f}")
    print("HARDWARE TAGS:", tags_in(tx2) or "(none)")
    print("\n--- reply ---\n" + tx2.strip())
except Exception as e:
    bt = getattr(e, "read", lambda: b"")() or b""
    print("CLAUDE ERROR:", str(e)[:120], bt.decode("utf-8", "ignore")[:400])

if RUN_GROK:
    print("\n\n========== GROK non-reasoning (his real model, best-effort via api.x.ai) ==========")
    xkey = os.environ.get("XAI_API_KEY", "")
    if not xkey:
        ct = subprocess.run(["bash", "-lc", "crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
        m = re.search(r'XAI_API_KEY\s*=\s*"?([^"\n]+)"?', ct)
        if m: xkey = m.group(1).strip()
    if not xkey:
        print("(no XAI_API_KEY)")
    else:
        gbody = {"model": GROK_MODEL, "messages": [{"role": "system", "content": system}] + msgs,
                 "temperature": 0.85, "top_p": 0.95, "max_tokens": 400}
        try:
            req = urllib.request.Request("https://api.x.ai/v1/chat/completions", data=json.dumps(gbody).encode(),
                headers={"Content-Type": "application/json", "Authorization": "Bearer " + xkey})
            gr = json.loads(urllib.request.urlopen(req, timeout=120).read())
            g = ((gr.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            print("HARDWARE TAGS:", tags_in(g) or "(none)")
            print("\n--- reply ---\n" + g.strip())
        except Exception as e:
            bt = getattr(e, "read", lambda: b"")() or b""
            print("GROK ERROR (model may only exist on the local endpoint):",
                  str(e)[:100], bt.decode("utf-8", "ignore")[:200])

print(f"\n(Claude total ~${total:.3f} — saved nowhere)")
