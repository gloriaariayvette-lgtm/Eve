#!/usr/bin/env python3
"""patch_avatar_router.py — Aegis. Phase 1: Claude-primary in the LIVE avatar_chat via a single model router,
grok as the fallback, reasoning -> touch bubble. Reversible: backs up server.py, verifies every anchor,
syntax-checks the result, and ABORTS WITHOUT WRITING if anything is off. Writes model_router.py alongside.

Run once. Then restart the Vintos server for it to take effect. Key setup (one-time, your key, never in repo):
    printf '%s' 'sk-ant-...' > ~/.vintos/anthropic-key && chmod 600 ~/.vintos/anthropic-key
"""
import os, glob, time, shutil

SERVER = next((p for p in (["/home/gloria/Vintos/server.py"]
              + glob.glob(os.path.expanduser("~/Vintos/server.py"))) if os.path.isfile(p)), None)
if not SERVER:
    print("server.py not found"); raise SystemExit(1)
VDIR = os.path.dirname(SERVER)

ROUTER_SRC = r'''"""model_router.py — single source of model truth for Vintos text surfaces.
Claude drives chat/avatar; grok is the fallback (hard refusal, error, toggle=grok, or a forced-turn window).
Voice and Gemma calls are never routed here. Flip a surface in CLAUDE_SURFACES / the mode file, not across jobs."""
import os, json
from datetime import datetime
import httpx

_HOME = os.path.expanduser("~")
_MODE_FILE = os.path.join(_HOME, ".vintos", "model-mode.json")
_KEY_FILE = os.path.join(_HOME, ".vintos", "anthropic-key")
CLAUDE_MODEL = "claude-opus-4-8"
CLAUDE_SURFACES = {"avatar"}   # add "chat" in phase 2

def _anthropic_key():
    k = os.environ.get("ANTHROPIC_API_KEY", "")
    if k: return k
    try: return open(_KEY_FILE).read().strip()
    except Exception: return ""

def read_mode():
    try: return json.load(open(_MODE_FILE))
    except Exception: return {"mode": "claude", "force_grok_turns": 0}

def write_mode(m):
    try:
        os.makedirs(os.path.dirname(_MODE_FILE), exist_ok=True)
        json.dump(m, open(_MODE_FILE, "w"))
    except Exception: pass

def arm_grok_turns(n=1):
    """Regenerate/one-turn override: force grok for the next n turns."""
    m = read_mode(); m["force_grok_turns"] = max(int(m.get("force_grok_turns", 0) or 0), int(n)); write_mode(m)

def _consume_forced():
    m = read_mode()
    n = int(m.get("force_grok_turns", 0) or 0)
    if n > 0:
        m["force_grok_turns"] = n - 1; write_mode(m); return True
    return False

async def _grok(convo, params, endpoint, headers, model, system_text):
    body = {"model": model, "messages": [{"role": "system", "content": system_text}] + convo,
            "max_tokens": params.get("max_tokens", 400),
            "temperature": params.get("temperature", 0.85),
            "top_p": params.get("top_p", 0.95)}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(endpoint, headers=headers, json=body)
        return r.json()["choices"][0]["message"]["content"]

async def _claude(system_text, convo, params, reason):
    key = _anthropic_key()
    if not key: raise RuntimeError("no anthropic key")
    if reason:
        thinking = {"type": "adaptive", "display": "summarized"}
        max_tok = max(int(params.get("max_tokens", 400)), 1200)
    else:
        thinking = {"type": "disabled"}
        max_tok = max(int(params.get("max_tokens", 400)), 128)
    body = {"model": CLAUDE_MODEL, "max_tokens": max_tok,
            "system": [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}],
            "messages": convo, "thinking": thinking}
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post("https://api.anthropic.com/v1/messages", json=body,
            headers={"content-type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": key})
        d = r.json()
    if d.get("type") == "error" or d.get("stop_reason") == "refusal":
        return None, ""
    think = "".join(b.get("thinking", "") for b in d.get("content", []) if b.get("type") == "thinking")
    text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    return (text or None), think

async def route_reply(surface, system_text, convo, params, grok_endpoint, grok_headers, grok_model, reason=True):
    """Returns (reply, reasoning, model_used). The grok path is the safety net."""
    if surface not in CLAUDE_SURFACES:
        return await _grok(convo, params, grok_endpoint, grok_headers, grok_model, system_text), "", "grok(surface)"
    if read_mode().get("mode") == "grok":
        return await _grok(convo, params, grok_endpoint, grok_headers, grok_model, system_text), "", "grok(toggle)"
    if _consume_forced():
        return await _grok(convo, params, grok_endpoint, grok_headers, grok_model, system_text), "", "grok(forced)"
    why = "grok(refusal)"
    try:
        reply, reasoning = await _claude(system_text, convo, params, reason)
        if reply is not None:
            return reply, reasoning, "claude"
    except Exception as e:
        why = "grok(error:%s)" % str(e)[:40]
    return await _grok(convo, params, grok_endpoint, grok_headers, grok_model, system_text), "", why
'''

# ---- anchors in the LIVE avatar_chat (first def) ----
lines = open(SERVER, encoding="utf-8").read().split("\n")
S = next((i for i, l in enumerate(lines) if l.lstrip().startswith("async def avatar_chat")), None)
if S is None:
    print("avatar_chat not found — aborting, nothing changed."); raise SystemExit(1)
col = len(lines[S]) - len(lines[S].lstrip())
END = S + 1
while END < len(lines):
    l = lines[END]
    if l.strip() and (len(l) - len(l.lstrip())) <= col and (l.lstrip().startswith(("async def ", "def ", "@app"))):
        break
    END += 1

def find_one(pred, lo, hi, label):
    hits = [i for i in range(lo, hi) if pred(lines[i])]
    if len(hits) != 1:
        print(f"anchor '{label}': expected 1, found {len(hits)} — aborting, nothing changed."); raise SystemExit(1)
    return hits[0]

i_start = find_one(lambda l: l.strip() == "async with httpx.AsyncClient(timeout=60) as client:", S, END, "grok-block-start")
i_end   = find_one(lambda l: l.strip() == 'reply = data["choices"][0]["message"]["content"]', S, END, "grok-block-end")
i_ret   = find_one(lambda l: l.strip() == 'return {"reply": reply}', S, END, "return")
if not (i_start < i_end < i_ret):
    print("anchors out of order — aborting, nothing changed."); raise SystemExit(1)

router_block = '''        # -- model router (single source of truth): Claude primary, grok fallback --
        import model_router as _mr
        _reason = (not _felt_now) and ("touched" not in (msg.message or "").lower())
        try:
            reply, _claude_reasoning, _model_used = await _mr.route_reply(
                "avatar", messages[0]["content"], messages[1:], params,
                f"{LM_STUDIO_API}/chat/completions", LLM_AUTH_HEADERS,
                "grok-4.20-0309-non-reasoning", reason=_reason)
        except Exception as _rte:
            print("[router] fatal:", _rte, flush=True)
            reply, _claude_reasoning, _model_used = "", "", "error"'''.split("\n")

return_block = '''        try:
            if _claude_reasoning and _claude_reasoning.strip():
                _impp = os.path.join(MEMORY, "imprints.json")
                try: _impd = json.load(open(_impp))
                except Exception: _impd = []
                _impd.append({"narrative": _claude_reasoning.strip()[:400], "salience": 0.9,
                              "timestamp": datetime.now().isoformat(), "source": "claude-reasoning"})
                json.dump(_impd[-200:], open(_impp, "w"))
        except Exception as _ime:
            print("[reasoning->bubble]", _ime, flush=True)
        return {"reply": reply, "model": _model_used}'''.split("\n")

out = []
i = 0
while i < len(lines):
    if i == i_start:
        out.extend(router_block); i = i_end + 1; continue
    if i == i_ret:
        out.extend(return_block); i += 1; continue
    out.append(lines[i]); i += 1
newtext = "\n".join(out)

# syntax gate — abort without writing if the result won't compile
try:
    compile(newtext, SERVER, "exec")
except SyntaxError as e:
    print(f"SYNTAX CHECK FAILED ({e}) — aborting, server.py untouched."); raise SystemExit(1)

bak = SERVER + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(SERVER, bak)
open(SERVER, "w", encoding="utf-8").write(newtext)
open(os.path.join(VDIR, "model_router.py"), "w", encoding="utf-8").write(ROUTER_SRC)

print("OK — patched.")
print(f"  backup:       {bak}")
print(f"  server.py:    replaced grok block L{i_start+1}-{i_end+1}, return L{i_ret+1} (avatar_chat L{S+1}-{END})")
print(f"  new module:   {os.path.join(VDIR, 'model_router.py')}")
print("\nNEXT:")
print("  1) one-time key:  printf '%s' 'sk-ant-...' > ~/.vintos/anthropic-key && chmod 600 ~/.vintos/anthropic-key")
print("  2) restart the Vintos server so the change loads")
print("  3) send an avatar message; check the log for '[router] avatar served by claude'")
print(f"  revert anytime:   cp {bak} {SERVER} && rm {os.path.join(VDIR, 'model_router.py')}")
