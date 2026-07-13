#!/usr/bin/env python3
"""ask_llm_auth_patch.py — add the missing Authorization header to the engine's ask_llm.

ask_llm builds a curl POST to x.ai with ONLY a Content-Type header — no Authorization. So every
call 401s, json.loads sees an error body, d["choices"] throws, and the bare `except: return ""`
swallows it. Result: nightly_run formation, hypothesis testing, form_hypotheses — everything that
routes through ask_llm — has silently returned "" and done nothing. This inserts the auth header.

Self-locating (regex, whitespace-tolerant), idempotent, backs up causality-engine.py. Only the
ask_llm curl matches (the review helper uses requests.post, not a curl list).
"""
import io, os, re, time, shutil

F = os.environ.get("CENG_PATH", os.path.expanduser("~/Vintos/causality-engine.py"))
s = io.open(F, encoding="utf-8").read()

if 'Authorization: Bearer " + (os.environ.get("XAI_API_KEY")' in s:
    print("already patched — skipping"); raise SystemExit(0)

# match:  "-H", "Content-Type: application/json", "-d", payload]
pat = re.compile(r'("-H",\s*"Content-Type: application/json",)(\s*)("-d",\s*payload\])')
m = pat.search(s)
if not m:
    print("MISS: ask_llm curl (Content-Type ... -d payload) not found"); raise SystemExit(1)

ins = ('\\1\n'
       '             "-H", "Authorization: Bearer " + (os.environ.get("XAI_API_KEY") or ""),\n'
       '             \\3')
s2 = s[:m.start()] + pat.sub(ins, s[m.start():], count=1)

shutil.copy(F, F + ".bak-auth-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s2)
print("PATCHED — ask_llm now sends Authorization: Bearer $XAI_API_KEY (backup written)")
