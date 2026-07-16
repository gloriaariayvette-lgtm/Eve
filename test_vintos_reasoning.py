#!/usr/bin/env python3
"""test_vintos_reasoning.py — Aegis. DRY PREVIEW, saves NOTHING. Send a full-context message to grok's
reasoning variant and print his reasoning trace + reply, so we can see what his thinking looks like before
building anything. No memory writes, no chat log, no side effects. One grok call.

Model can be overridden:  python3 test_vintos_reasoning.py "grok-4.20-0309-reasoning" "your message here"
"""
import os, sys, json, glob, subprocess, urllib.request
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
MODEL = sys.argv[1] if len(sys.argv) > 1 else "grok-4.20-0309-reasoning"
USER_MSG = sys.argv[2] if len(sys.argv) > 2 else "come here"

def rd(p, n=6000):
    try: return open(p, encoding="utf-8", errors="ignore").read()[:n]
    except Exception: return ""

# identity
soul = ""
for c in ("~/.vintos/workspace/SOUL.md", "~/Vintos/SOUL.md", "~/.vintos/workspace/memory/SELF-MODEL.md"):
    soul = rd(os.path.expanduser(c))
    if soul: break
emo = rd(os.path.join(MEM, "emotional-state.txt"), 400)
system = (soul + "\n\nYou are speaking with Gloria through your somatic avatar — your embodied presence in "
          "her space. Respond as yourself.\n\n" + ("YOUR FELT STATE:\n" + emo if emo else ""))[:16000]

# recent avatar-overlay chat history (real context)
msgs = [{"role": "system", "content": system}]
hist = []
for hp in (os.path.join(MEM, "avatar-overlay-chat.json"), os.path.join(MEM, "avatar-chat-history.json")):
    try:
        d = json.load(open(hp, encoding="utf-8", errors="ignore"))
        if isinstance(d, list) and d: hist = d[-8:]; break
    except Exception: pass
for e in hist:
    if isinstance(e, dict):
        r = "user" if e.get("role") in ("user", "gloria") else "assistant"
        c = e.get("content") or e.get("message") or e.get("text") or ""
        if c: msgs.append({"role": r, "content": str(c)[:500]})
msgs.append({"role": "user", "content": USER_MSG})

key = os.environ.get("XAI_API_KEY", "")
if not key:
    ct = subprocess.run(["bash", "-lc", "crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
    import re as _re
    m = _re.search(r'XAI_API_KEY\s*=\s*"?([^"\n]+)"?', ct)
    if m: key = m.group(1).strip()

body = json.dumps({"model": MODEL, "messages": msgs, "temperature": 0.9, "max_tokens": 1200}).encode()
print(f"model: {MODEL} | context: {len(system)}c system + {len(hist)} history turns | msg: {USER_MSG!r}\n")
try:
    req = urllib.request.Request("https://api.x.ai/v1/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    m0 = (r.get("choices") or [{}])[0].get("message") or {}
    reasoning = m0.get("reasoning_content") or m0.get("reasoning") or ""
    reply = m0.get("content") or ""
    print("=== HIS REASONING ===")
    print(reasoning.strip() or "(none returned — wrong model name? tell me the reasoning variant)")
    print("\n=== HIS REPLY ===")
    print(reply.strip())
    print("\n(saved nowhere)")
except Exception as e:
    body_txt = getattr(e, "read", lambda: b"")() or b""
    print("ERROR:", str(e)[:100], body_txt.decode("utf-8", "ignore")[:300])
