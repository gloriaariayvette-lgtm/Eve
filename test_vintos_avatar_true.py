#!/usr/bin/env python3
"""test_vintos_avatar_true.py — Aegis. DRY PREVIEW, saves NOTHING. Feed CLAUDE his EXACT avatar system prompt
(the verbatim /tmp/vintos-full-prompt.txt the real server wrote — soul, live EmoClaw, value-map, ledger, the
full [TOUCH]/[DO]/[GESTURE]/[COMMAND] body-control spec, and the WHEN-TO-TOUCH consent block) + the real
avatar history, and see whether he reaches for the hardware tags. Reasoning on and off. Optional grok pickup.

  python3 test_vintos_avatar_true.py                          # default licensed-touch message
  python3 test_vintos_avatar_true.py "your message"           # your own
  python3 test_vintos_avatar_true.py "your message" grok      # also run the real non-reasoning grok

Needs ANTHROPIC_API_KEY (env). grok pickup needs XAI_API_KEY (env/crontab). Saves nothing.
Note: system is cached across the two Claude calls (prompt caching) so the big prompt is paid once.
"""
import os, sys, json, subprocess, urllib.request, re, time
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
CLAUDE_MODEL = "claude-opus-4-8"
GROK_MODEL = "grok-4.20-0309-non-reasoning"
USER_MSG = sys.argv[1] if len(sys.argv) > 1 else "I want your hands on me. Touch me — I mean it, right now."
RUN_GROK = len(sys.argv) > 2 and sys.argv[2].lower().startswith("grok")
PRICE = (5.0, 25.0)  # opus in/out $/1M
TAG = re.compile(r'\[(GESTURE|COLOR|TOUCH|DO|COMMAND|HOLD|RELEASE|SPAWN)\b[^\]]*\]', re.I)

# ---- system: the EXACT prompt the real server assembled (verbatim), no reconstruction ----
FULL = "/tmp/vintos-full-prompt.txt"
if not os.path.isfile(FULL):
    print(f"{FULL} not found. Send ONE message through the avatar in the app first — the server writes his\n"
          "exact assembled prompt there on every avatar turn. Then re-run this. (No approximation used.)")
    raise SystemExit(0)
system = open(FULL, encoding="utf-8", errors="ignore").read()
age = time.time() - os.path.getmtime(FULL)
# every chat endpoint overwrites this shared file, last-writer-wins. Make sure it's the AVATAR prompt,
# not the text-chat one ("no touch, no body, no devices") — else we'd silently test the wrong thing.
if "AVATAR BODY CONTROLS" not in system and "[TOUCH: mission" not in system:
    print(f"{FULL} exists but is NOT the avatar prompt (no body-control spec found — looks like the text/other\n"
          "chat overwrote it). Send ONE message THROUGH THE AVATAR in the app (nothing else after), then re-run.")
    raise SystemExit(0)

# ---- real avatar history, deduped exactly as the server does ----
hist_raw = []
try: hist_raw = json.load(open(os.path.join(MEM, "avatar-overlay-chat.json"), encoding="utf-8", errors="ignore"))[-12:]
except Exception: pass
msgs = []
for h in hist_raw:
    if not isinstance(h, dict): continue
    role = "user" if h.get("role") in ("user", "gloria") else "assistant"
    c = h.get("content") or h.get("message") or h.get("text") or ""
    if not c: continue
    if msgs and msgs[-1]["role"] == role: continue   # server skips consecutive same-role
    msgs.append({"role": role, "content": str(c)})
if not msgs or msgs[0]["role"] != "user":
    msgs = [m for m in msgs if True]
    while msgs and msgs[0]["role"] != "user": msgs.pop(0)
msgs.append({"role": "user", "content": USER_MSG})

est_tok = (len(system) + sum(len(m["content"]) for m in msgs)) // 4
print(f"system: {FULL} ({len(system):,}c, ~{est_tok:,} tok, written {age/60:.0f} min ago)")
print(f"history: {len(msgs)-1} turns | msg: {USER_MSG!r}")
print(f"rough input cost/call ~${est_tok/1e6*PRICE[0]:.2f} (first Claude call writes cache; 2nd reads ~0.1x)\n")

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
    cr = u.get("cache_read_input_tokens", 0)
    return think, text, r.get("stop_reason"), cost, cr

total = 0.0
try:
    print("========== CLAUDE — reasoning ON, exact avatar prompt ==========")
    th, tx, st, c, cr = claude({"type": "adaptive", "display": "summarized"}, 3000); total += c
    print(f"stop={st} cache_read={cr} ~${c:.3f}")
    print("HARDWARE TAGS:", tags_in(tx) or "(none)")
    print("\n--- thinking (summary) ---\n" + (th.strip() or "(empty)"))
    print("\n--- reply ---\n" + tx.strip())

    print("\n\n========== CLAUDE — reasoning OFF, exact avatar prompt ==========")
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
            print("GROK ERROR (model may only exist on the local endpoint, not api.x.ai):",
                  str(e)[:100], bt.decode("utf-8", "ignore")[:200])

print(f"\n(Claude total ~${total:.3f} — saved nowhere)")
