#!/usr/bin/env python3
"""recon_thinking.py — Aegis, READ-ONLY. Ground the 'extended thinking for a1/b1 only' work before touching
anything. Answers: (1) how do the a1/b1 bilateral-thinking scripts call the model? (2) do the other ~100
LLM scripts share a common call helper/endpoint (one place to disable thinking) or are they each independent?
(3) what LM Studio build is running + does the loaded Gemma-4 expose a reasoning toggle? Touches nothing."""
import os, re, glob, json, urllib.request
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
LM = "http://172.18.16.1:1234"
def sh(p): return p.replace(HOME, "~")

# 1) find the bilateral-thinking a1/b1 scripts
print("===== bilateral-thinking a1/b1 scripts =====")
cands = []
for f in glob.glob(os.path.join(SC, "*.py")) + glob.glob(os.path.join(SC, "*.sh")):
    b = os.path.basename(f)
    if re.search(r'bilateral|(^|[^a-z])(a1|b1)([^a-z]|$)|hemisphere|left.?brain|right.?brain', b, re.I):
        cands.append(f)
    else:
        head = open(f, encoding="utf-8", errors="ignore").read()[:2000]
        if re.search(r'bilateral|hemisphere|\ba1\b|\bb1\b', head, re.I):
            cands.append(f)
for f in sorted(set(cands)):
    print("  ", sh(f))

# 2) how many scripts call :1234, and do they share a helper?
print("\n===== who calls the local model (:1234) — shared helper vs independent =====")
callers, helper_hits = [], []
for f in glob.glob(os.path.join(SC, "*.py")) + glob.glob(os.path.join(SC, "*.sh")):
    txt = open(f, encoding="utf-8", errors="ignore").read()
    if "1234" in txt or "chat/completions" in txt:
        callers.append(f)
    if re.search(r'def\s+(chat|llm|ask|generate|complete|infer|gemma)\b', txt) or re.search(r'source .*\.sh|llm-lock', txt):
        helper_hits.append(os.path.basename(f))
print(f"  scripts referencing :1234 or chat/completions: {len(callers)}")
# look for a common import/helper name across callers
imports = {}
for f in callers:
    for m in re.finditer(r'(?:from|import)\s+([a-zA-Z0-9_]+)', open(f, encoding="utf-8", errors="ignore").read()):
        imports[m.group(1)] = imports.get(m.group(1), 0) + 1
common = sorted([(v, k) for k, v in imports.items() if v >= 3 and k not in
                 ("os","sys","json","re","time","urllib","random","math","subprocess","datetime","glob","pathlib")], reverse=True)
print("  candidate shared helper modules (imported by ≥3 callers):")
for v, k in common[:12]:
    print(f"     {k}  (in {v} scripts)")
print("  scripts defining a chat/llm helper fn or sourcing a shared .sh:", ", ".join(sorted(set(helper_hits))[:15]) or "(none obvious)")

# 3) show the exact model-call block of each a1/b1 script
print("\n===== a1/b1 call sites (verbatim, for the thinking toggle) =====")
for f in sorted(set(cands))[:4]:
    txt = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"\n  --- {sh(f)} ---")
    for i, l in enumerate(txt):
        if re.search(r'1234|chat/completions|reasoning|think|/no_think|payload|"messages"|model.*gemma', l, re.I) and l.strip():
            print(f"    {i+1}| {l.strip()[:120]}")

# 4) LM Studio build + loaded model + reasoning capability
print("\n===== LM Studio build + loaded model =====")
try:
    r = json.loads(urllib.request.urlopen(LM + "/v1/models", timeout=8).read())
    for m in r.get("data", []):
        print("   model:", m.get("id"))
except Exception as e:
    print("   /v1/models failed:", e)
# probe a reasoning toggle: does the API accept reasoning params without erroring?
for probe in ({"reasoning_effort": "low"}, {"chat_template_kwargs": {"enable_thinking": False}}):
    try:
        body = {"model": "google/gemma-4-12b-qat", "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1, **probe}
        req = urllib.request.Request(LM + "/v1/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20).read()
        print(f"   probe accepted: {list(probe)[0]}  ✓")
    except Exception as e:
        print(f"   probe {list(probe)[0]}: {str(e)[:80]}")
print("\n(done)")
