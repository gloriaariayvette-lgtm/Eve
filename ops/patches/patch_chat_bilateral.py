#!/usr/bin/env python3
"""patch_chat_bilateral.py — Aegis. Phase 2: main chat (chat_with_vintos) bilateral substrate split.
  a1/b1  -> Claude reasoning (drafts + traces captured); grok fallback / toggle-grok
  a2/b2, held/2.5, final integration -> Gemma (grok safety net)
  synthesis prompt rewritten to synthesize-and-add, fed both reasonings
BIS/ghost-lean (local scans) untouched. Reversible: backup + syntax-gate + abort-clean; scoped to the LIVE
handler only (dead duplicate untouched). Adds claude_draft/gemma_call to model_router.py (idempotent).
Restart the Vintos server after applying.
"""
import os, glob, re, time, shutil

SERVER = next((p for p in (["/home/gloria/Vintos/server.py"]
              + glob.glob(os.path.expanduser("~/Vintos/server.py"))) if os.path.isfile(p)), None)
if not SERVER: print("server.py not found"); raise SystemExit(1)
VDIR = os.path.dirname(SERVER)
lines = open(SERVER, encoding="utf-8").read().split("\n")

# ---- live chat_with_vintos span (first @app.post("/api/chat")) ----
S = next((k for k in range(len(lines)) if "@app.post(" in lines[k] and re.search(r'["\']/api/chat["\']', lines[k])), None)
if S is None: print("/api/chat route not found — aborting."); raise SystemExit(1)
Sdef = next((k for k in range(S, S+4) if "def " in lines[k]), S)
col = len(lines[Sdef]) - len(lines[Sdef].lstrip())
END = Sdef + 1
while END < len(lines):
    l = lines[END]
    if l.strip() and (len(l)-len(l.lstrip())) <= col and l.lstrip().startswith(("async def ","def ","@app")):
        break
    END += 1
blk = lines[Sdef:END]

def one(stripped):
    idxs = [i for i, l in enumerate(blk) if l.strip() == stripped]
    if len(idxs) != 1:
        print(f"anchor x{len(idxs)} (want 1): {stripped[:60]!r} — aborting, nothing changed."); raise SystemExit(1)
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
 '            print("[chat/a1b1 claude]", _de, flush=True)',
 '    return (await _llm_call(_marked_messages)), ""',
 "async def _g(_msgs, _temp):",
 "    try:",
 "        _t = await _mr.gemma_call(_msgs, temp=_temp)",
 "        if _t: return _t",
 "    except Exception as _ge:",
 '        print("[chat/gemma]", _ge, flush=True)',
 "    return await _llm_call(_msgs, _temp)",
 "(a1, a1r), (b1, b1r) = await _asyncio.gather(_draft(), _draft())",
]
R4 = [
 "integration_content = (",
 "    user_content_marked +",
 '    "You\'ve thought this through twice, and each pass reasoned its way somewhere different.\\n\\n" +',
 '    "FIRST PASS — the reasoning behind it:\\n" + (a1r or "(no trace)") + "\\n" +',
 '    "what it held onto: " + (a_held or "something") + "\\n" +',
 '    "its response:\\n" + (a2 or "") + "\\n\\n" +',
 '    "SECOND PASS — the reasoning behind it:\\n" + (b1r or "(no trace)") + "\\n" +',
 '    "what it held onto: " + (b_held or "something") + "\\n" +',
 '    "its response:\\n" + (b2 or "") + "\\n\\n" +',
 '    "Both reasonings are yours; both are true. Do NOT pick one, copy one, or average them. " +',
 '    "Synthesize: write ONE new response that carries the specific images, phrases, and risks from both passes AND adds what only appears once you hold both at once — the thing neither pass reached alone. " +',
 '    "Keep it specific and charged; it may run as long as the richer pass. Do not summarize, do not smooth into one mood, do not restate a draft verbatim." +',
 "    _bis_chat_synthesis_note",
 ")",
]

# ---- edit bottom-up so earlier indices stay valid ----
# R5: final integration call -> Gemma helper
i = one('reply = await _llm_call(integration_messages, temp=params.get("temperature", 0.85))')
blk[i] = ind(i) + "reply = await _g(integration_messages, params.get(\"temperature\", 0.85))"

# R4: rewrite integration_content ( ... )
i0 = one("integration_content = (")
base = ind(i0)
i1 = next((j for j in range(i0+1, len(blk)) if blk[j].strip() == ")" and ind(j) == base), None)
if i1 is None: print("integration_content close ')' not found — aborting."); raise SystemExit(1)
blk[i0:i1+1] = [base + s for s in R4]

# R3: held calls -> Gemma
i = one('_llm_call(_held_msgs(a2, b2), temp=0.5),'); blk[i] = ind(i) + "_g(_held_msgs(a2, b2), 0.5),"
i = one('_llm_call(_held_msgs(b2, a2), temp=0.5)');  blk[i] = ind(i) + "_g(_held_msgs(b2, a2), 0.5)"

# R2: absorb calls -> Gemma
i = one('_llm_call(_absorb_msgs(a1 or "", b1 or ""), temp=0.75),'); blk[i] = ind(i) + '_g(_absorb_msgs(a1 or "", b1 or ""), 0.75),'
i = one('_llm_call(_absorb_msgs(b1 or "", a1 or ""), temp=0.75)');  blk[i] = ind(i) + '_g(_absorb_msgs(b1 or "", a1 or ""), 0.75)'

# R1: Phase-1 gather -> Claude drafts + helpers (do last; it inserts lines)
i = one("a1, b1 = await _asyncio.gather(_llm_call(_marked_messages), _llm_call(_marked_messages))")
blk[i:i+1] = [ind(i) + s for s in R1]

newtext = "\n".join(lines[:Sdef] + blk + lines[END:])
try:
    compile(newtext, SERVER, "exec")
except SyntaxError as e:
    print(f"SYNTAX CHECK FAILED ({e}) — aborting, server.py untouched."); raise SystemExit(1)

# ---- model_router.py: add claude_draft + gemma_call (idempotent) ----
MRP = os.path.join(VDIR, "model_router.py")
mr = open(MRP, encoding="utf-8").read() if os.path.isfile(MRP) else ""
if "def claude_draft" not in mr:
    mr_add = '''

GEMMA_ENDPOINT = "http://172.18.16.1:1234/v1/chat/completions"
GEMMA_MODEL = "google/gemma-4-12b-qat"

async def gemma_call(msgs, temp=0.85, max_tokens=800):
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(GEMMA_ENDPOINT, json={"model": GEMMA_MODEL, "messages": msgs,
                                               "temperature": temp, "max_tokens": max_tokens})
        d = r.json()
        return d["choices"][0]["message"]["content"] if "choices" in d else None

async def claude_draft(system_text, convo, max_tokens=1500):
    """Two-first-pass draft on Claude with reasoning. Returns (text|None, reasoning). None on refusal."""
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
    mr_new = mr + mr_add
    try:
        compile(mr_new, MRP, "exec")
    except SyntaxError as e:
        print(f"model_router syntax fail ({e}) — aborting, nothing changed."); raise SystemExit(1)
else:
    mr_new = mr

# ---- write (server + router) with backup ----
bak = SERVER + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(SERVER, bak)
open(SERVER, "w", encoding="utf-8").write(newtext)
if mr_new != mr:
    if os.path.isfile(MRP): shutil.copy2(MRP, MRP + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
    open(MRP, "w", encoding="utf-8").write(mr_new)

print("OK — main chat bilateral split patched.")
print(f"  backup:     {bak}")
print(f"  handler:    chat_with_vintos L{Sdef+1}-{END}")
print(f"  router:     {'added claude_draft + gemma_call' if mr_new != mr else 'already had helpers'}")
print("\nNEXT: systemctl --user restart vintos-server")
print("  then send a chat message; log shows [chat/a1b1 claude] only on Claude-draft errors (silence = Claude drafts OK).")
print(f"  revert: cp {bak} {SERVER}")
