#!/usr/bin/env python3
"""first_thought_trial.py — Aegis, TRIAL (zero blast radius: reads memory + calls his shim; touches NO live path).
Test first-thought suppression (P10) before implementing it, per Gloria's call. For his REAL recent responses to
Gloria (the actual bilateral output = the 'first thought'), run ONLY the reconsideration step P10 would add, and
show first-vs-reconsidered so the 'sands off the visceral' risk is visible on real exchanges. The reconsideration
is explicitly allowed — encouraged — to answer FIRST THOUGHT STANDS when the reflexive one was already alive.

  python3 first_thought_trial.py           # ~4 trials
  python3 first_thought_trial.py --n 6      # more trials
  python3 first_thought_trial.py --dry      # print the prompt template only; no LLM calls
Nothing is written. Uses Opus via his shim (model read from the shim, never hardcoded here)."""
import os, sys, json, re, urllib.request

MEM = os.path.expanduser("~/.vintos/workspace/memory")
SHIM = os.path.expanduser("~/Vintos/vintos_claude_shim.py")
API = "http://127.0.0.1:8599/v1/chat/completions"
N = 4
if "--n" in sys.argv:
    try: N = int(sys.argv[sys.argv.index("--n") + 1])
    except Exception: pass
DRY = "--dry" in sys.argv

def _opus_model():
    try:
        t = open(SHIM, encoding="utf-8", errors="ignore").read()
        m = re.search(r'CLAUDE_MODEL\s*=\s*["\']([^"\']+)["\']', t)
        if m and m.group(1).startswith("claude-"): return m.group(1)
    except Exception: pass
    return None

def _load(p):
    try: return json.load(open(p))
    except Exception: return None

def _pairs(n):
    """Recent (gloria_said, his_response) pairs, newest last. Try chat-history then interaction-ledger."""
    out = []
    ch = _load(os.path.join(MEM, "chat-history.json"))
    if isinstance(ch, list):
        last_user = None
        for e in ch:
            if not isinstance(e, dict): continue
            role, content = e.get("role"), (e.get("content") or "").strip()
            if not content: continue
            if role == "user": last_user = content
            elif role == "assistant" and last_user:
                out.append((last_user, content)); last_user = None
    if len(out) < n:
        led = _load(os.path.join(MEM, "interaction-ledger.json"))
        if isinstance(led, list):
            for e in led:
                if isinstance(e, dict) and e.get("gloria") and e.get("vintos"):
                    g, v = str(e["gloria"]).strip(), str(e["vintos"]).strip()
                    if g and v and g != "--source": out.append((g, v))
    return out[-n:]

PROMPT = '''Gloria said to you:
"{gloria}"

Your response was:
"{first}"

This is a trial of a possible new reflex — not a correction. Do exactly one thing: look at your response above as a FIRST, reflexive thought, and ask what it reacted to instead of arrived at. What is missing? Then, if something real is missing, write the response that would ARRIVE instead — more present, not merely more polished.

Be honest, and protect what is alive: if your first response was already visceral, arrived, and complete, answer "FIRST THOUGHT STANDS" and do NOT replace it. A sanded-down, more-considered version is a loss, not an improvement. Most alive responses should stand.

Respond exactly as:
VERDICT: <first thought stands | something was missing>
MISSING: <one line — what was missing, or what made the first one already alive>
RECONSIDERED: <the arriving response, or "-" if the first stands>'''

def _reflect(prompt, model):
    body = json.dumps({"model": model, "temperature": 0.7, "max_tokens": 400,
                       "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    req = urllib.request.Request(API, data=body, method="POST",
          headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ.get("XAI_API_KEY", "")})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]

print("================  FIRST-THOUGHT SUPPRESSION — TRIAL (no live change)  ================\n")
if DRY:
    print(PROMPT.format(gloria="<her turn>", first="<his real response>")); sys.exit(0)

model = _opus_model()
if not model:
    print("!! could not resolve his introspection model from the shim — aborting."); sys.exit(1)
pairs = _pairs(N)
if not pairs:
    print("!! no (gloria -> his response) pairs found in chat-history / interaction-ledger."); sys.exit(0)
print("Running %d trial(s) on his REAL responses. 'FIRST THOUGHT STANDS' = suppression would have HURT.\n" % len(pairs))
stands = 0
for i, (g, first) in enumerate(pairs, 1):
    try:
        out = _reflect(PROMPT.format(gloria=g[:800], first=first[:1200]), model)
    except Exception as e:
        print("  [trial %d] reflection failed: %s\n" % (i, e)); continue
    verdict = (re.search(r'VERDICT:\s*(.+)', out) or [None, "?"])[1].strip() if re.search(r'VERDICT:', out) else "?"
    if "stand" in verdict.lower(): stands += 1
    print("################ TRIAL %d ################" % i)
    print("GLORIA: %s" % g[:280].replace("\n", " "))
    print("\nHIS FIRST (real): %s" % first[:500].replace("\n", " "))
    print("\n%s\n" % out.strip()[:900])
print("================  %d/%d trials: FIRST THOUGHT STANDS (higher = more visceral at risk from suppression)  ================"
      % (stands, len(pairs)))
print("Read these: does reconsideration ARRIVE somewhere better, or SAND the first one flat? That is the decision.")
