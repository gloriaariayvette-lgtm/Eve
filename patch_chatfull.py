#!/usr/bin/env python3
"""patch_chatfull.py — Aegis. THE REAL main-chat handler: chat_full_context (/api/chat/full). One consolidated
patch: a1/b1 -> Claude reasoning (traces captured); a2/b2 + held -> Gemma; final synthesis -> Claude fed both
drafts + both traces, speaking only to Gloria; per-turn trace to /tmp/vintos-chat-trace.json. Reversible:
backup + syntax-gate + abort-clean; scoped to the live handler. Adds claude_draft/gemma_call to model_router
(idempotent). Restart after."""
import os, glob, re, time, shutil
SERVER = next((p for p in (["/home/gloria/Vintos/server.py"]
              + glob.glob(os.path.expanduser("~/Vintos/server.py"))) if os.path.isfile(p)), None)
if not SERVER: print("server.py not found"); raise SystemExit(1)
VDIR = os.path.dirname(SERVER)
lines = open(SERVER, encoding="utf-8").read().split("\n")

S = next((k for k in range(len(lines)) if "@app.post(" in lines[k] and re.search(r'["\']/api/chat/full["\']', lines[k])), None)
if S is None: print("/api/chat/full not found — aborting."); raise SystemExit(1)
Sdef = next((k for k in range(S, S+4) if "def " in lines[k]), S)
col = len(lines[Sdef]) - len(lines[Sdef].lstrip())
END = Sdef + 1
while END < len(lines):
    l = lines[END]
    if l.strip() and (len(l)-len(l.lstrip())) <= col and l.lstrip().startswith(("async def ","def ","@app")):
        break
    END += 1
blk = lines[Sdef:END]
if any("vintos-chat-trace.json" in l for l in blk):
    print("already patched (trace present) — aborting to avoid double-apply."); raise SystemExit(0)

def one(stripped):
    idxs = [i for i, l in enumerate(blk) if l.strip() == stripped]
    if len(idxs) != 1:
        print(f"anchor x{len(idxs)} (want 1): {stripped[:56]!r} — aborting, nothing changed."); raise SystemExit(1)
    return idxs[0]
def ind(i): return blk[i][:len(blk[i]) - len(blk[i].lstrip())]

R1 = [
 "import model_router as _mr",
 '_chat_grok = _mr.read_mode().get("mode") == "grok"',
 "async def _draft():",
 "    if not _chat_grok:",
 "        try:",
 '            _t, _rr = await _mr.claude_draft(_marked_messages[0]["content"], _marked_messages[1:])',
 "            if _t: return _t, _rr",
 "        except Exception as _de:",
 '            print("[chatfull/a1b1 claude]", _de, flush=True)',
 '    return (await _llm_call(_marked_messages)), ""',
 "async def _g(_msgs, _temp):",
 "    try:",
 "        _t = await _mr.gemma_call(_msgs, temp=_temp)",
 "        if _t: return _t",
 "    except Exception as _ge:",
 '        print("[chatfull/gemma]", _ge, flush=True)',
 "    return await _llm_call(_msgs, _temp)",
 "(a1, a1r), (b1, b1r) = await _asyncio.gather(_draft(), _draft())",
]
R_INT = [
 "integration_content = (",
 "    user_content_marked +",
 '    "You have just thought this through in two parallel passes. Below is your own private working — reasoning and drafts — which Gloria never sees:\\n\\n" +',
 '    "PASS ONE reasoning: " + (a1r or "(none)") + "\\n" +',
 '    "PASS ONE held onto: " + (a_held or "something") + "\\n" +',
 '    "PASS ONE wrote:\\n" + (a2 or "") + "\\n\\n" +',
 '    "PASS TWO reasoning: " + (b1r or "(none)") + "\\n" +',
 '    "PASS TWO held onto: " + (b_held or "something") + "\\n" +',
 '    "PASS TWO wrote:\\n" + (b2 or "") + "\\n\\n" +',
 '    "Now write your real reply to Gloria — one message, present, in your own voice, answering what she just said. " +',
 '    "Let both passes reason under it: keep the sharpest specific images, wants, and risks from both, and add what only becomes clear holding both at once. Build one thing, fuller than either draft — do not pick one, copy one, or average them. " +',
 '    "Speak only TO her. Nothing about passes, reasoning, versions, holding, your architecture, or your process reaches her — she sees only what you say. Say the real thing, to her." +',
 "    _bis_chat_synthesis_note",
 ")",
]
R_FINAL = [
 "reply = None",
 "if not _chat_grok:",
 "    try:",
 '        reply, _final_reason = await _mr.claude_draft(integration_messages[0]["content"], integration_messages[1:])',
 "    except Exception as _fe:",
 '        print("[chatfull/final claude]", _fe, flush=True)',
 "        reply = None",
 "if not reply:",
 '    reply = await _g(integration_messages, params.get("temperature", 0.85))',
]
T = [
 "try:",
 "    import json as _tj",
 '    _ffr = locals().get("_final_reason")',
 '    _tj.dump({"gloria": msg.message,',
 '              "a1_model": ("claude" if a1r else "grok"), "a1r": a1r, "a1": a1,',
 '              "b1_model": ("claude" if b1r else "grok"), "b1r": b1r, "b1": b1,',
 '              "a2": a2, "b2": b2, "a_held": a_held, "b_held": b_held,',
 '              "final_model": ("claude" if _ffr else "gemma_or_grok"), "final": reply},',
 '             open("/tmp/vintos-chat-trace.json", "w"), indent=2, ensure_ascii=False)',
 '    print(f"[chatfull/trace] a1={\'claude\' if a1r else \'grok\'} b1={\'claude\' if b1r else \'grok\'} final={\'claude\' if _ffr else \'gemma/grok\'}", flush=True)',
 "except Exception as _te:",
 '    print("[chatfull/trace]", _te, flush=True)',
]

# --- edits, bottom-up so indices stay valid ---
# E6: trace insert before tag-strip
ti = [i for i, l in enumerate(blk) if "_re_do.sub" in l and "reply" in l]
if len(ti) != 1: print(f"tag-strip anchor x{len(ti)} — aborting."); raise SystemExit(1)
i = ti[0]; blk[i:i] = [ind(i) + s for s in T]

# E5: final call -> Claude
i = one("reply = await _llm_call(integration_messages, temp=params.get(\"temperature\", 0.85))")
blk[i:i+1] = [ind(i) + s for s in R_FINAL]

# E4: integration_content -> reasoning-fed
i0 = one("integration_content = (")
base = ind(i0)
i1 = next((j for j in range(i0+1, len(blk)) if blk[j].strip() == ")" and ind(j) == base), None)
if i1 is None: print("integration close ')' not found — aborting."); raise SystemExit(1)
blk[i0:i1+1] = [base + s for s in R_INT]

# E3: held -> Gemma
i = one("_llm_call(_held_msgs(a2, b2), temp=0.5),"); blk[i] = ind(i) + "_g(_held_msgs(a2, b2), 0.5),"
i = one("_llm_call(_held_msgs(b2, a2), temp=0.5)");  blk[i] = ind(i) + "_g(_held_msgs(b2, a2), 0.5)"

# E2: absorb -> Gemma
i = one('_llm_call(_absorb_msgs(a1 or "", b1 or ""), temp=0.75),'); blk[i] = ind(i) + '_g(_absorb_msgs(a1 or "", b1 or ""), 0.75),'
i = one('_llm_call(_absorb_msgs(b1 or "", a1 or ""), temp=0.75)');  blk[i] = ind(i) + '_g(_absorb_msgs(b1 or "", a1 or ""), 0.75)'

# E1: a1/b1 gather -> Claude drafts + helpers (last; inserts lines)
i = one("a1, b1 = await _asyncio.gather(_llm_call(_marked_messages), _llm_call(_marked_messages))")
blk[i:i+1] = [ind(i) + s for s in R1]

newtext = "\n".join(lines[:Sdef] + blk + lines[END:])
try:
    compile(newtext, SERVER, "exec")
except SyntaxError as e:
    print(f"SYNTAX CHECK FAILED ({e}) — aborting, server.py untouched."); raise SystemExit(1)

# model_router: ensure claude_draft + gemma_call
MRP = os.path.join(VDIR, "model_router.py")
mr = open(MRP, encoding="utf-8").read() if os.path.isfile(MRP) else ""
mr_new = mr
if mr and "def claude_draft" not in mr:
    mr_new = mr + '''

GEMMA_ENDPOINT = "http://172.18.16.1:1234/v1/chat/completions"
GEMMA_MODEL = "google/gemma-4-12b-qat"

async def gemma_call(msgs, temp=0.85, max_tokens=800):
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(GEMMA_ENDPOINT, json={"model": GEMMA_MODEL, "messages": msgs,
                                               "temperature": temp, "max_tokens": max_tokens})
        d = r.json()
        return d["choices"][0]["message"]["content"] if "choices" in d else None

async def claude_draft(system_text, convo, max_tokens=1500):
    key = _anthropic_key()
    if not key: raise RuntimeError("no anthropic key")
    convo = list(convo)
    while convo and convo[0].get("role") != "user":
        convo = convo[1:]
    body = {"model": CLAUDE_MODEL, "max_tokens": max_tokens,
            "system": [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}],
            "messages": convo, "thinking": {"type": "adaptive", "display": "summarized"}}
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post("https://api.anthropic.com/v1/messages", json=body,
            headers={"content-type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": key})
        d = r.json()
    if d.get("type") == "error" or d.get("stop_reason") == "refusal":
        return None, ""
    think = "".join(b.get("thinking", "") for b in d.get("content", []) if b.get("type") == "thinking")
    text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    return (text or None), think
'''
elif not mr:
    print("model_router.py missing — run patch_avatar_router first (Phase 1)."); raise SystemExit(1)
if mr_new != mr:
    try: compile(mr_new, MRP, "exec")
    except SyntaxError as e: print(f"router syntax fail ({e}) — aborting."); raise SystemExit(1)

bak = SERVER + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(SERVER, bak); open(SERVER, "w", encoding="utf-8").write(newtext)
if mr_new != mr:
    shutil.copy2(MRP, MRP + ".bak-" + time.strftime("%Y%m%d-%H%M%S")); open(MRP, "w", encoding="utf-8").write(mr_new)

print("OK — /api/chat/full (chat_full_context) patched: Claude a1/b1, Gemma middle, Claude final, trace on.")
print(f"  backup:  {bak}")
print(f"  handler: chat_full_context L{Sdef+1}-{END}")
print(f"  router:  {'added claude_draft+gemma_call' if mr_new != mr else 'already had helpers'}")
print("\nNEXT: systemctl --user restart vintos-server ; send ONE chat msg ; then:")
print("  python3 -m json.tool /tmp/vintos-chat-trace.json")
print(f"  revert: cp {bak} {SERVER}")
