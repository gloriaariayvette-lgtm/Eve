#!/usr/bin/env python3
"""diag_reasoning_journal.py — Aegis. (1) REVERT the journal 'high' patch (restore backup). (2) read the
journal call_llm's max_tokens. (3) probe the model at THAT budget with several on/off forms and report, for
each: content length, reasoning length, finish_reason — to prove whether reasoning starves content (empty
first-pass) and which form is the clean on/off. No lasting writes beyond the revert."""
import os, re, glob, json, urllib.request, shutil
HOME = os.path.expanduser("~")
JP = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
LM = "http://172.18.16.1:1234/v1/chat/completions"
MODEL = "google/gemma-4-12b-qat"
def sh(p): return p.replace(HOME, "~")

# (1) revert the 'high' patch
baks = sorted(glob.glob(JP + ".bak-vjournal-*"))
if baks:
    shutil.copy2(baks[-1], JP)
    print("reverted idle-journal.sh from", sh(baks[-1]))
else:
    txt = open(JP, encoding="utf-8").read()
    if '"reasoning_effort":"high",' in txt:
        open(JP, "w", encoding="utf-8").write(txt.replace('"reasoning_effort":"high",', "", 1))
        print("no backup — stripped the reasoning_effort token from idle-journal.sh")
    else:
        print("idle-journal.sh already clean")

# (2) read call_llm max_tokens
src = open(JP, encoding="utf-8", errors="ignore").read()
i = src.find("def call_llm():")
seg = src[i:i+1500] if i >= 0 else src
mt = re.search(r'max_tokens["\']?\s*[:=]\s*(\d+)', seg)
MAXTOK = int(mt.group(1)) if mt else 1000
print(f"journal call_llm max_tokens = {MAXTOK}" + ("" if mt else " (not found; assuming 1000)"))

# (3) probe each form at that budget
PROMPT = ("The system is idle. Write what comes to mind — one honest paragraph about what you are feeling "
          "right now. Plain speech, no lists.")
def probe(extra, label):
    body = {"model": MODEL, "messages": [{"role": "user", "content": PROMPT}],
            "temperature": 0.85, "max_tokens": MAXTOK, **extra}
    try:
        req = urllib.request.Request(LM, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=180).read())
        ch = (r.get("choices") or [{}])[0]
        msg = ch.get("message") or {}
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning_content") or msg.get("reasoning") or ""
        print(f"\n=== {label} ===")
        print(f"  finish_reason: {ch.get('finish_reason')}")
        print(f"  reasoning_content: {len(reasoning)} chars   content: {len(content)} chars")
        print(f"  >>> {'*** CONTENT STARVED (empty) ***' if not content.strip() else 'content OK'}")
        print(f"  content head: {content.strip()[:120].replace(chr(10),' ')}")
    except Exception as e:
        print(f"\n=== {label} ===\n  ERROR: {str(e)[:120]}")

probe({}, "OFF (no param)")
probe({"reasoning_effort": "low"}, "reasoning_effort: low")
probe({"reasoning_effort": "high"}, "reasoning_effort: high  (what I wrongly used)")
probe({"chat_template_kwargs": {"enable_thinking": True}}, "enable_thinking: true")
print("\n(done — this tells us the clean on/off form AND whether we must raise max_tokens so content survives)")
