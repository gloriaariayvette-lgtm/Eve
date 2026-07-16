#!/usr/bin/env python3
"""patch_introspection_claude.py — Aegis. introspection.sh: a1/b1 -> Claude reasoning (override the Gemma
drafts right after they're assigned), final synthesis -> Claude (Gemma fallback). Middle stays Gemma.
Reversible: backup + syntax-check of the embedded Python block + abort-clean on any mismatch."""
import os, glob, re, time, shutil
P = next((p for p in ([os.path.expanduser("~/Vintos/introspection.sh")]) if os.path.isfile(p)), None)
if not P: print("introspection.sh not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")
if any("_claude_sync" in l for l in lines):
    print("already patched — aborting."); raise SystemExit(0)

def one(stripped):
    idx = [i for i, l in enumerate(lines) if l.strip() == stripped]
    if len(idx) != 1: print(f"anchor x{len(idx)} (want 1): {stripped[:50]!r} — aborting."); raise SystemExit(1)
    return idx[0]

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
 "",
]
OVERRIDE = [
 "# a1/b1 -> Claude reasoning (override the Gemma drafts)",
 "try:",
 "    _ia1, _ = _claude_sync(system, prompt, reasoning=True)",
 "    _ib1, _ = _claude_sync(system, prompt, reasoning=True)",
 "    if _ia1: a1 = _ia1",
 "    if _ib1: b1 = _ib1",
 "    import sys as _cs; print('[intro] a1/b1 on claude', file=_cs.stderr, flush=True)",
 "except Exception as _ice:",
 "    import sys as _cs; print(f'[intro/a1b1 claude] {_ice}', file=_cs.stderr, flush=True)",
]
FINAL = [
 "final, _ = _claude_sync(system, integration, reasoning=True, max_tokens=1500)",
 "if not final:",
 "    final = call_llm([{'role': 'system', 'content': system}, {'role': 'user', 'content': integration}], temperature=0.85, max_tokens=1500)",
]

# edits bottom-up
# final block (572-575): final = call_llm( ... )
fi = one("final = call_llm(")
fj = next((j for j in range(fi+1, len(lines)) if lines[j].strip() == ")"), None)
if fj is None: print("final ')' not found — aborting."); raise SystemExit(1)
lines[fi:fj+1] = FINAL

# override after a1,b1 = results
ai = one("a1, b1 = results[0], results[1]")
lines[ai+1:ai+1] = OVERRIDE

# helper before base_msgs
bi = one("base_msgs = [")
lines[bi:bi] = HELPER

# syntax-check the inserted snippets in isolation (the surrounding script already runs;
# a bash+heredoc file can't be compiled whole). All inserts sit at module indent, matching context.
newtext = "\n".join(lines)
for grp, nm in ((HELPER, "HELPER"), (OVERRIDE, "OVERRIDE"), (FINAL, "FINAL")):
    try: compile("\n".join(grp), "<" + nm + ">", "exec")
    except SyntaxError as e:
        print(f"inserted-snippet SYNTAX FAIL in {nm} ({e}) — aborting, untouched."); raise SystemExit(1)

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(newtext)
print(f"OK — introspection.sh: a1/b1 + final on Claude, middle Gemma.\n  backup: {bak}")
print("test:   bash ~/Vintos/introspection.sh   (watch for '[intro] a1/b1 on claude'; entry should read clean)")
print(f"revert: cp {bak} {P}")
