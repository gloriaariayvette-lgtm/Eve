#!/usr/bin/env python3
"""patch_idle_journal_claude.py — Aegis. idle-journal.sh: a1/b1 -> Claude reasoning (grok fallback only on
failure, no waste), final synthesis -> Claude (grok fallback). Middle (absorb/held/audits) left on grok for
now — Gemma swap is the next step. Backup + snippet syntax-check + abort-clean. Reversible."""
import os, time, shutil
P = os.path.expanduser("~/Vintos/idle-journal.sh")
if not os.path.isfile(P): print("idle-journal.sh not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")
if any("_claude_sync" in l for l in lines):
    print("already patched — aborting."); raise SystemExit(0)

def one(pred, label):
    idx = [i for i, l in enumerate(lines) if pred(l)]
    if len(idx) != 1: print(f"anchor '{label}' x{len(idx)} (want 1) — aborting."); raise SystemExit(1)
    return idx[0]
def ind(i): return lines[i][:len(lines[i]) - len(lines[i].lstrip())]

HELPER = [
 "def _claude_sync(system_text, user_text, reasoning=False, max_tokens=1500):",
 "    import urllib.request as _u, json as _j, os as _o",
 '    _k = _o.environ.get("ANTHROPIC_API_KEY", "")',
 "    if not _k:",
 '        try: _k = open(_o.path.expanduser("~/.vintos/anthropic-key")).read().strip()',
 "        except Exception: _k = ''",
 "    if not _k: return None, ''",
 '    _body = {"model": "claude-opus-4-8", "max_tokens": max_tokens,',
 '             "system": [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}],',
 '             "messages": [{"role": "user", "content": user_text}],',
 '             "thinking": ({"type": "adaptive", "display": "summarized"} if reasoning else {"type": "disabled"})}',
 '    _rq = _u.Request("https://api.anthropic.com/v1/messages", data=_j.dumps(_body).encode(),',
 '                     headers={"content-type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": _k})',
 "    try: _d = _j.loads(_u.urlopen(_rq, timeout=180).read())",
 "    except Exception: return None, ''",
 '    if _d.get("type") == "error" or _d.get("stop_reason") == "refusal": return None, ""',
 '    _t = "".join(b.get("text", "") for b in _d.get("content", []) if b.get("type") == "text")',
 '    _th = "".join(b.get("thinking", "") for b in _d.get("content", []) if b.get("type") == "thinking")',
 "    return (_t or None), _th",
]
R3 = [
 '_raw = (_claude_sync(_synthesis_system, integration_prompt, True)[0] or "")',
 "import sys as _js; print('[journal] final on claude' if _raw else '[journal] final fell to grok', file=_js.stderr, flush=True)",
 "if not _raw:",
 '    r3 = requests.post("https://api.x.ai/v1/chat/completions",',
 '        headers={"Authorization": "Bearer " + os.environ.get("XAI_API_KEY", "")},',
 '        json={"model": "grok-4.20-0309-non-reasoning",',
 '              "messages": [{"role": "system", "content": _synthesis_system},',
 '                           {"role": "user", "content": integration_prompt}],',
 '              "temperature": 0.3, "max_tokens": 1400}, timeout=600)',
 "    _raw = _safe_extract(r3)",
]

# validate inserted snippets
for grp, nm in ((HELPER, "HELPER"), (R3, "R3")):
    try: compile("\n".join(grp), "<" + nm + ">", "exec")
    except SyntaxError as e: print(f"snippet {nm} bad ({e}) — aborting."); raise SystemExit(1)

# R3 block: r3 = requests.post( ... ) through _raw = _safe_extract(r3)
i0 = one(lambda l: l.strip().startswith("r3 = requests.post("), "r3-start")
i1 = one(lambda l: l.strip() == "_raw = _safe_extract(r3)", "r3-raw")
if not (i0 < i1): print("r3 block out of order — aborting."); raise SystemExit(1)
base = ind(i0)
lines[i0:i1+1] = [base + s for s in R3]

# b1 then a1 (single-line replaces)
ib = one(lambda l: l.strip() == "b1 = call_llm()", "b1")
lines[ib] = ind(ib) + "b1 = (_claude_sync(system_msg, user_msg, True)[0] or call_llm())"
ia = one(lambda l: l.strip() == "a1 = call_llm()", "a1")
lines[ia] = ind(ia) + "a1 = (_claude_sync(system_msg, user_msg, True)[0] or call_llm())"

# helper before a1
lines[ia:ia] = [ind(ia) + s for s in HELPER]

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write("\n".join(lines))
print(f"OK — idle-journal.sh: a1/b1 + final on Claude (grok fallback), middle still grok.\n  backup: {bak}")
print("test:   bash ~/Vintos/idle-journal.sh   (watch for '[journal] final on claude'; entry should read clean)")
print(f"revert: cp {bak} {P}")
