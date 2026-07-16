#!/usr/bin/env python3
"""patch_chat_claude_final.py — Aegis. Correct the pipeline: FINAL synthesis = Claude (fed both drafts + both
reasoning traces), grok/gemma only as net. Rewrites integration_content to a reasoning-fed, speak-only-to-her
prompt and swaps the final call from Gemma(_g) to Claude(claude_draft). Reversible: backup + syntax-gate +
abort-clean; scoped to the LIVE chat_with_vintos. Restart after."""
import os, glob, re, time, shutil
SERVER = next((p for p in (["/home/gloria/Vintos/server.py"]
              + glob.glob(os.path.expanduser("~/Vintos/server.py"))) if os.path.isfile(p)), None)
if not SERVER: print("server.py not found"); raise SystemExit(1)
lines = open(SERVER, encoding="utf-8").read().split("\n")

S = next((k for k in range(len(lines)) if "@app.post(" in lines[k] and re.search(r'["\']/api/chat["\']', lines[k])), None)
if S is None: print("/api/chat not found — aborting."); raise SystemExit(1)
Sdef = next((k for k in range(S, S+4) if "def " in lines[k]), S)
col = len(lines[Sdef]) - len(lines[Sdef].lstrip())
END = Sdef + 1
while END < len(lines):
    l = lines[END]
    if l.strip() and (len(l)-len(l.lstrip())) <= col and l.lstrip().startswith(("async def ","def ","@app")):
        break
    END += 1
blk = lines[Sdef:END]
def indof(s): return s[:len(s)-len(s.lstrip())]

R_INT = [
 "integration_content = (",
 "    user_content_marked +",
 '    "You have just thought this through in two parallel passes. Below is your own private working — reasoning and drafts — which Gloria never sees:\\n\\n" +',
 '    "PASS ONE reasoning: " + (a1r or "(none)") + "\\n" +',
 '    "PASS ONE held onto: " + (a_held or "something") + "\\n" +',
 '    "PASS ONE wrote:\\n" + (a2 or "") + "\\n\\n" +',
 '    "PASS TWO reasoning: " + (b1r or "(none)") + "\\n" +',
 '    "PASS TWO held onto: " + (b_held or "something") + "\\n" +',
 '    "PASS TWO wrote:\\n" + (b2 or "") + "\\n\\n" +',
 '    "Now write your real reply to Gloria — one message, present, in your own voice, answering what she just said. " +',
 '    "Let both passes reason under it: keep the sharpest specific images, wants, and risks from both, and add what only becomes clear holding both at once. Build one thing, fuller than either draft — do not pick one, copy one, or average them. " +',
 '    "Speak only TO her. Nothing about passes, reasoning, versions, holding, your architecture, or your process reaches her — she sees only what you say. Say the real thing, to her." +',
 "    _bis_chat_synthesis_note",
 ")",
]
R_FINAL = [
 "reply = None",
 "if not _chat_grok:",
 "    try:",
 '        reply, _final_reason = await _mr.claude_draft(integration_messages[0]["content"], integration_messages[1:])',
 "    except Exception as _fe:",
 '        print("[chat/final claude]", _fe, flush=True)',
 "        reply = None",
 "if not reply:",
 '    reply = await _g(integration_messages, params.get("temperature", 0.85))',
]

# E2 first (higher index): swap final call Gemma -> Claude
fa = 'reply = await _g(integration_messages, params.get("temperature", 0.85))'
fi = [i for i, l in enumerate(blk) if l.strip() == fa]
if len(fi) != 1: print(f"final-call anchor x{len(fi)} (want 1) — aborting."); raise SystemExit(1)
fbase = indof(blk[fi[0]])
blk[fi[0]:fi[0]+1] = [fbase + s for s in R_FINAL]

# E1: rewrite integration_content ( ... )
ci = [i for i, l in enumerate(blk) if l.strip() == "integration_content = ("]
if len(ci) != 1: print(f"integration_content anchor x{len(ci)} (want 1) — aborting."); raise SystemExit(1)
i0 = ci[0]; cbase = indof(blk[i0])
i1 = next((j for j in range(i0+1, len(blk)) if blk[j].strip() == ")" and indof(blk[j]) == cbase), None)
if i1 is None: print("integration_content close ')' not found — aborting."); raise SystemExit(1)
blk[i0:i1+1] = [cbase + s for s in R_INT]

newtext = "\n".join(lines[:Sdef] + blk + lines[END:])
try:
    compile(newtext, SERVER, "exec")
except SyntaxError as e:
    print(f"SYNTAX CHECK FAILED ({e}) — aborting, untouched."); raise SystemExit(1)
bak = SERVER + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(SERVER, bak); open(SERVER, "w", encoding="utf-8").write(newtext)
print("OK — final synthesis is now Claude, fed both reasonings, speaks only to her.")
print(f"  backup: {bak}\nNEXT: systemctl --user restart vintos-server")
