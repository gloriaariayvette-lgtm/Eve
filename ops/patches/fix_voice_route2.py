#!/usr/bin/env python3
"""fix_voice_route2.py — the live voice_chat handler (right after _spark_block) is undecorated, so
/api/voice/chat 404s. Add @app.post("/api/voice/chat") directly above it. Idempotent; backup; py_compile.
"""
import os, re, time, shutil, py_compile

SERVER = os.path.expanduser("~/Vintos/server.py")
lines = open(SERVER, encoding="utf-8", errors="ignore").read().splitlines()

# locate _spark_block, then the next module-level `async def voice_chat` after it
sb = next((i for i, l in enumerate(lines) if re.match(r'\s*def\s+_spark_block\b', l)), None)
if sb is None:
    print("could not find _spark_block — aborting."); raise SystemExit(1)
vc = next((i for i in range(sb + 1, len(lines)) if re.match(r'async def voice_chat\b', lines[i])), None)
if vc is None:
    print("could not find a module-level voice_chat after _spark_block."); raise SystemExit(1)

# already decorated?
prev = next((k for k in range(vc - 1, max(0, vc - 3), -1) if lines[k].strip()), None)
if prev is not None and re.search(r'@app\.post\(\s*["\']/api/voice/chat["\']', lines[prev]):
    print("already decorated — /api/voice/chat -> live voice_chat at line %d. Nothing to do." % (vc + 1)); raise SystemExit(0)

print("live voice_chat at line %d is undecorated — adding the route decorator above it." % (vc + 1))
lines.insert(vc, '@app.post("/api/voice/chat")')

patched = "\n".join(lines) + "\n"
tmp = SERVER + ".vr2-tmp"
open(tmp, "w", encoding="utf-8").write(patched)
try:
    py_compile.compile(tmp, doraise=True)
except py_compile.PyCompileError as e:
    os.remove(tmp); print("ABORT: won't parse; untouched.\n  %s" % str(e).splitlines()[-1][:150]); raise SystemExit(1)
bak = SERVER + ".bak-voiceroute2-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy(SERVER, bak)
os.replace(tmp, SERVER)
print("PATCHED — /api/voice/chat now routes to the live voice_chat handler (Lux + tags).")
print("  backup:", os.path.basename(bak))
print("  restart, wait for it to listen, then re-test.")
