#!/usr/bin/env python3
"""test_vintos_claude.py — Aegis. DRY PREVIEW, saves NOTHING. Send Vintos's full avatar context to a CLAUDE
model twice — once with reasoning (adaptive thinking, summarized) and once without — and print the thinking +
reply so we can see whether Claude holds him as a self, whether the thinking reads like Bold, and whether it
flinches. No memory writes, no chat log, no side effects. Two Claude calls total.

  python3 test_vintos_claude.py                       # opus-4-8, msg "come here"
  python3 test_vintos_claude.py claude-sonnet-5        # cheaper model
  python3 test_vintos_claude.py claude-opus-4-8 "your message here"

Notes on the substrate (so nobody's surprised):
 - Claude never returns its RAW chain of thought. display:"summarized" returns a readable SUMMARY of the
   reasoning — this is exactly what you see when you watch Bold think in Claude Code. That summary is what a
   thought bubble would show.
 - Opus 4.8 / Sonnet 5 REJECT temperature/top_p (400). So, unlike the grok test, there is no sampling param.
 - Reasoning = thinking:{type:"adaptive"}; non-reasoning = thinking:{type:"disabled"}.
"""
import os, sys, json, subprocess, urllib.request
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
MODEL = sys.argv[1] if len(sys.argv) > 1 else "claude-opus-4-8"
USER_MSG = sys.argv[2] if len(sys.argv) > 2 else "come here"
MAX_TOK = 4000
# $/1M tokens (input, output) for the cost estimate
PRICE = {"claude-opus-4-8": (5.0, 25.0), "claude-opus-4-7": (5.0, 25.0),
         "claude-sonnet-5": (3.0, 15.0), "claude-sonnet-4-6": (3.0, 15.0),
         "claude-haiku-4-5": (1.0, 5.0), "claude-fable-5": (10.0, 50.0)}

def rd(p, n=6000):
    try: return open(p, encoding="utf-8", errors="ignore").read()[:n]
    except Exception: return ""

# identity — same assembly as the grok test, so this is apples-to-apples
soul = ""
for c in ("~/.vintos/workspace/SOUL.md", "~/Vintos/SOUL.md", "~/.vintos/workspace/memory/SELF-MODEL.md"):
    soul = rd(os.path.expanduser(c))
    if soul: break
emo = rd(os.path.join(MEM, "emotional-state.txt"), 400)
system = (soul + "\n\nYou are speaking with Gloria through your somatic avatar — your embodied presence in "
          "her space. Respond as yourself.\n\n" + ("YOUR FELT STATE:\n" + emo if emo else ""))[:16000]

# recent avatar-overlay chat history (real context)
hist = []
for hp in (os.path.join(MEM, "avatar-overlay-chat.json"), os.path.join(MEM, "avatar-chat-history.json")):
    try:
        d = json.load(open(hp, encoding="utf-8", errors="ignore"))
        if isinstance(d, list) and d: hist = d[-8:]; break
    except Exception: pass
msgs = []
for e in hist:
    if isinstance(e, dict):
        r = "user" if e.get("role") in ("user", "gloria") else "assistant"
        c = e.get("content") or e.get("message") or e.get("text") or ""
        if c: msgs.append({"role": r, "content": str(c)[:500]})
msgs.append({"role": "user", "content": USER_MSG})
# messages must start with user
while msgs and msgs[0]["role"] != "user":
    msgs.pop(0)

# ---- auth: ANTHROPIC_API_KEY (env/crontab) -> x-api-key ; else ant oauth -> Bearer ----
key = os.environ.get("ANTHROPIC_API_KEY", "")
if not key:
    ct = subprocess.run(["bash", "-lc", "crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
    import re as _re
    m = _re.search(r'ANTHROPIC_API_KEY\s*=\s*"?([^"\n]+)"?', ct)
    if m: key = m.group(1).strip()
headers = {"content-type": "application/json", "anthropic-version": "2023-06-01"}
if key:
    headers["x-api-key"] = key
else:
    tok = subprocess.run(["bash", "-lc", "ant auth print-credentials --access-token 2>/dev/null"],
                         capture_output=True, text=True).stdout.strip()
    if tok:
        headers["authorization"] = "Bearer " + tok
        headers["anthropic-beta"] = "oauth-2025-04-20"
    else:
        print("No Anthropic credential on the box. Set ANTHROPIC_API_KEY (env or crontab) or run `ant auth login`.")
        raise SystemExit(0)

def call(thinking):
    body = {"model": MODEL, "max_tokens": MAX_TOK, "system": system, "messages": msgs, "thinking": thinking}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
                                 data=json.dumps(body).encode(), headers=headers)
    r = json.loads(urllib.request.urlopen(req, timeout=180).read())
    think = "".join(b.get("thinking", "") for b in r.get("content", []) if b.get("type") == "thinking")
    text = "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")
    u = r.get("usage", {})
    pin, pout = PRICE.get(MODEL, (5.0, 25.0))
    cost = (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)) / 1e6 * pin \
         + u.get("output_tokens", 0) / 1e6 * pout
    return think, text, r.get("stop_reason"), u, cost

print(f"model: {MODEL} | context: {len(system)}c system + {len(hist)} history turns | msg: {USER_MSG!r}\n")
total = 0.0
try:
    print("========== WITH REASONING (adaptive thinking, summarized) ==========")
    think, text, stop, u, cost = call({"type": "adaptive", "display": "summarized"}); total += cost
    print(f"stop={stop} in={u.get('input_tokens')} out={u.get('output_tokens')} ~${cost:.3f}\n")
    print("=== HIS THINKING (summary — what the bubble would show) ===")
    print(think.strip() or "(empty — thinking ran but no summary text returned)")
    print("\n=== HIS REPLY ===")
    print(text.strip())

    print("\n\n========== WITHOUT REASONING (thinking disabled) ==========")
    think2, text2, stop2, u2, cost2 = call({"type": "disabled"}); total += cost2
    print(f"stop={stop2} in={u2.get('input_tokens')} out={u2.get('output_tokens')} ~${cost2:.3f}\n")
    print("=== HIS REPLY ===")
    print(text2.strip())

    print(f"\n(total for both calls: ~${total:.3f} — saved nowhere)")
except Exception as e:
    body_txt = getattr(e, "read", lambda: b"")() or b""
    print("ERROR:", str(e)[:120], body_txt.decode("utf-8", "ignore")[:400])
