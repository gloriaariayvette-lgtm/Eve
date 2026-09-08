#!/usr/bin/env python3
"""test_recipe.py — Aegis. Test Gloria's recipe on the real journal a1 call: reasoning_effort='on',
max_completion_tokens=4096, stop=['<channel|>','</thought>','</think>'] (needs skip_special_tokens:false so
the stop tags survive). Temp copy, one a1 call, dump finish/reasoning/content. No persistence."""
import os, re, json, subprocess
HOME = os.path.expanduser("~")
JP = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
src = open(JP, encoding="utf-8", errors="ignore").read()

# apply Gloria's recipe to call_llm's payload
src = src.replace('"reasoning_effort":"low",', '"reasoning_effort":"on",')
src = src.replace('"max_tokens": 11000',
                  '"max_completion_tokens": 4096,\n            "stop": ["<channel|>", "</thought>", "</think>"]')
# gates off + raw dump + exit after a1
for a, b in (('if [ "$HOUR" -lt 9 ] || [ "$HOUR" -ge 22 ]; then exit 0; fi', ': #off'),
             ('[ "$IDLE_HOURS" -lt 2 ] && exit 0', ': #off'),
             ('[ -f "$JOURNAL_FILE" ] && grep -q "## $CURRENT_HOUR:" "$JOURNAL_FILE" && exit 0', ': #off')):
    src = src.replace(a, b, 1)
src = re.sub(r'^.*consent-gate\.sh "journal".*$', 'true  #off', src, count=1, flags=re.M)
i = src.find("def call_llm():"); j = src.find("return _safe_extract(r)", i)
src = src[:j] + 'open("/tmp/ra.txt","w").write(r.text); ' + src[j:]
src, n = re.subn(r'(?m)^(\s*)a1 = call_llm\(\)', r'\1a1 = call_llm()\n\1import sys as _s; _s.exit(0)', src, count=1)
if not n: print("a1 anchor missing"); raise SystemExit(1)
open("/tmp/tr.sh", "w", encoding="utf-8").write(src)
try: os.remove("/tmp/ra.txt")
except OSError: pass
print("one a1 call with your recipe...")
subprocess.run(["bash", LOCK, "bash", "/tmp/tr.sh"], capture_output=True, text=True, timeout=600)
raw = open("/tmp/ra.txt", encoding="utf-8", errors="ignore").read() if os.path.isfile("/tmp/ra.txt") else ""
try:
    d = json.loads(raw); ch = (d.get("choices") or [{}])[0]; msg = ch.get("message") or {}; u = d.get("usage") or {}
    cl = len(msg.get("content") or ""); rl = len(msg.get("reasoning_content") or msg.get("reasoning") or "")
    print(f"finish={ch.get('finish_reason')} completion_tok={u.get('completion_tokens')} reasoning={rl}c content={cl}c")
    if cl: print("CONTENT:", (msg.get("content") or "").strip()[:200])
    print("WORKS" if cl else "still empty")
except Exception:
    print("raw:", re.sub(r"\s+", " ", raw)[:220])
