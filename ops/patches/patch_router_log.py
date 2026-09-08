#!/usr/bin/env python3
"""patch_router_log.py — Aegis. Add the missing per-turn '[router] avatar served by <model>' log line to
avatar_chat. Idempotent, backs up, syntax-gates, aborts clean on mismatch."""
import os, glob, time, shutil
SERVER = next((p for p in (["/home/gloria/Vintos/server.py"]
              + glob.glob(os.path.expanduser("~/Vintos/server.py"))) if os.path.isfile(p)), None)
if not SERVER: print("server.py not found"); raise SystemExit(1)
text = open(SERVER, encoding="utf-8").read()
LOGLINE = '        print(f"[router] avatar served by {_model_used}", flush=True)'
if "[router] avatar served by" in text:
    print("already present — nothing to do."); raise SystemExit(0)
ANCHOR = '            reply, _claude_reasoning, _model_used = "", "", "error"'
if text.count(ANCHOR) != 1:
    print(f"anchor found {text.count(ANCHOR)}x (expected 1) — aborting, nothing changed."); raise SystemExit(1)
newtext = text.replace(ANCHOR, ANCHOR + "\n" + LOGLINE, 1)
try:
    compile(newtext, SERVER, "exec")
except SyntaxError as e:
    print(f"SYNTAX CHECK FAILED ({e}) — aborting."); raise SystemExit(1)
bak = SERVER + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(SERVER, bak); open(SERVER, "w", encoding="utf-8").write(newtext)
print(f"OK — added served-by log line. backup: {bak}\nrestart:  systemctl --user restart vintos-server")
