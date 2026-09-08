#!/usr/bin/env python3
"""patch_chat_trace.py — Aegis. Dump every bilateral stage of one chat turn (both drafts + reasonings, both
absorbs, held lines, final, and which model made each) to /tmp/vintos-chat-trace.json, plus a one-line log
summary. So we can SEE where the meta enters instead of guessing. Reversible: backup + syntax-gate +
abort-clean; scoped to the LIVE chat_with_vintos. Restart after; send ONE chat message; read the file."""
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

if any("vintos-chat-trace.json" in l for l in blk):
    print("trace already present — nothing to do."); raise SystemExit(0)

# insert before the device/command tag-strip line
ti = [i for i, l in enumerate(blk) if "_re_do.sub" in l and "reply" in l]
if len(ti) != 1: print(f"tag-strip anchor x{len(ti)} (want 1) — aborting."); raise SystemExit(1)
i = ti[0]; base = blk[i][:len(blk[i]) - len(blk[i].lstrip())]

T = [
 "try:",
 "    import json as _tj",
 '    _ffr = locals().get("_final_reason")',
 '    _tj.dump({"gloria": msg.message,',
 '              "a1_model": ("claude" if a1r else "grok"), "a1r": a1r, "a1": a1,',
 '              "b1_model": ("claude" if b1r else "grok"), "b1r": b1r, "b1": b1,',
 '              "a2": a2, "b2": b2, "a_held": a_held, "b_held": b_held,',
 '              "final_model": ("claude" if _ffr else "gemma_or_grok"), "final": reply},',
 '             open("/tmp/vintos-chat-trace.json", "w"), indent=2, ensure_ascii=False)',
 '    print(f"[chat/trace] a1={\'claude\' if a1r else \'grok\'} b1={\'claude\' if b1r else \'grok\'} final={\'claude\' if _ffr else \'gemma/grok\'} -> /tmp/vintos-chat-trace.json", flush=True)',
 "except Exception as _te:",
 '    print("[chat/trace]", _te, flush=True)',
]
blk[i:i] = [base + s for s in T]

newtext = "\n".join(lines[:Sdef] + blk + lines[END:])
try:
    compile(newtext, SERVER, "exec")
except SyntaxError as e:
    print(f"SYNTAX CHECK FAILED ({e}) — aborting, untouched."); raise SystemExit(1)
bak = SERVER + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(SERVER, bak); open(SERVER, "w", encoding="utf-8").write(newtext)
print(f"OK — per-turn trace added.\n  backup: {bak}\nNEXT: systemctl --user restart vintos-server ; send ONE chat msg ; then:")
print("  python3 -m json.tool /tmp/vintos-chat-trace.json")
