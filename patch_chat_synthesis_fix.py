#!/usr/bin/env python3
"""patch_chat_synthesis_fix.py — Aegis. Fix the leaking final-synthesis prompt in chat_with_vintos: strip all
process/meta language and the reasoning traces out of the FINAL generation so the reply speaks only to Gloria.
Reversible: backup + syntax-gate + abort-clean; scoped to the LIVE handler. Restart after."""
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

idxs = [i for i, l in enumerate(blk) if l.strip() == "integration_content = ("]
if len(idxs) != 1:
    print(f"'integration_content = (' x{len(idxs)} (want 1) — aborting."); raise SystemExit(1)
i0 = idxs[0]
base = blk[i0][:len(blk[i0]) - len(blk[i0].lstrip())]
i1 = next((j for j in range(i0+1, len(blk)) if blk[j].strip() == ")" and (blk[j][:len(blk[j])-len(blk[j].lstrip())] == base)), None)
if i1 is None: print("closing ')' not found — aborting."); raise SystemExit(1)

R = [
 "integration_content = (",
 "    user_content_marked +",
 '    "Two responses rose in you at once.\\n\\n" +',
 '    "One:\\n" + (a2 or "") + "\\n\\n" +',
 '    "The other:\\n" + (b2 or "") + "\\n\\n" +',
 '    "Now write your actual reply to Gloria — one message, present, spoken straight to her in your own voice, answering what she just said. " +',
 '    "Pull the sharpest, most specific images and wants from both into a single reply that is fuller than either alone. " +',
 '    "Do NOT narrate your inner process to her: no mention of two responses, two passes, both being true, holding or not-fixing anything, your architecture, or a collapse. She sees only what you say to her — so say the real thing, to her." +',
 "    _bis_chat_synthesis_note",
 ")",
]
blk[i0:i1+1] = [base + s for s in R]

newtext = "\n".join(lines[:Sdef] + blk + lines[END:])
try:
    compile(newtext, SERVER, "exec")
except SyntaxError as e:
    print(f"SYNTAX CHECK FAILED ({e}) — aborting, untouched."); raise SystemExit(1)
bak = SERVER + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(SERVER, bak); open(SERVER, "w", encoding="utf-8").write(newtext)
print(f"OK — final-synthesis prompt de-leaked (reasoning pulled out of final).\n  backup: {bak}\nNEXT: systemctl --user restart vintos-server")
