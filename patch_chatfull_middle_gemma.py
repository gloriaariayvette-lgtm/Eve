#!/usr/bin/env python3
"""patch_chatfull_middle_gemma.py — Aegis. Main chat's a1/b1+final are claude_draft (Claude), absorb/held are
_g/gemma_call (Gemma). Only two stray auxiliary grok calls remain in the LIVE chat_full_context (the _rm_
relational-mismatch pre-check ~L3008 and a pre-pass client.post ~L3773). Per spec those middle/auxiliary calls
are Gemma. Repoint ONLY those (scoped to the live function body) to the shim's /gemma route. Compiles server.py
before writing. Backup + abort-clean. Needs a server restart after."""
import os, re, time, shutil
P = os.path.expanduser("~/Vintos/server.py")
if not os.path.isfile(P): print("server.py not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")

defs = [i for i, l in enumerate(lines) if re.search(r'def chat_full_context', l)]
if not defs: print("chat_full_context not found"); raise SystemExit(1)
s = defs[0]
end = len(lines)
for i in range(s + 2, len(lines)):
    if re.match(r'(async def |def |@app\.)', lines[i]):
        end = i; break
print(f"live chat_full_context: L{s+1}..L{end}")

OLD = "https://api.x.ai/v1/chat/completions"
NEW = "http://127.0.0.1:8599/gemma/v1/chat/completions"
changed = []
for i in range(s, end):
    if OLD in lines[i]:
        lines[i] = lines[i].replace(OLD, NEW); changed.append(i + 1)
if not changed:
    print("no grok chat URL inside the live function (already redirected?) — aborting."); raise SystemExit(1)

newtext = "\n".join(lines)
try:
    compile(newtext, P, "exec")
except SyntaxError as e:
    print(f"result would not compile ({e}) — aborting, nothing written."); raise SystemExit(1)

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(newtext)
print(f"OK — repointed {len(changed)} stray grok call(s) to Gemma at lines {changed}. (dead dup + voice + fallback untouched)")
print(f"  backup: {bak}")
print("APPLY:  systemctl --user restart vintos-server")
print(f"revert: cp {bak} {P} && systemctl --user restart vintos-server")
