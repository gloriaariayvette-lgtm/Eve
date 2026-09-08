#!/usr/bin/env python3
"""fix_voice_route.py — POST /api/voice/chat is bound to the _spark_block() helper (a decorator got
wedged above it), so it returns the anti-repeat directive instead of running voice_chat. Remove ONLY
that misplaced decorator; the real handler keeps its own @app.post("/api/voice/chat"). Backup + py_compile.
"""
import os, re, time, shutil, py_compile

SERVER = os.path.expanduser("~/Vintos/server.py")
src = open(SERVER, encoding="utf-8", errors="ignore").read()
lines = src.splitlines()

DEC = re.compile(r'@app\.post\(\s*["\']/api/voice/chat["\']')

def next_nonblank(i):
    for k in range(i + 1, min(i + 4, len(lines))):
        if lines[k].strip(): return k
    return None

# find the decorator whose next def is _spark_block
target = None
for i, ln in enumerate(lines):
    if DEC.search(ln):
        n = next_nonblank(i)
        if n is not None and re.match(r'\s*(async\s+)?def\s+_spark_block\b', lines[n]):
            target = i; break

if target is None:
    print("no misrouted decorator found above _spark_block — maybe already fixed."); raise SystemExit(0)

# ensure another /api/voice/chat route remains for the real handler
remaining = [i for i, ln in enumerate(lines) if DEC.search(ln) and i != target]
if not remaining:
    print("ABORT: removing this would leave /api/voice/chat with NO handler. Not touching it.")
    print("  (the real voice_chat needs a decorator first — tell me and I'll add it instead.)"); raise SystemExit(1)

print("misrouted decorator at line %d (above _spark_block); real route remains at line(s) %s"
      % (target + 1, [r + 1 for r in remaining]))

del lines[target]
patched = "\n".join(lines) + ("\n" if src.endswith("\n") else "")
tmp = SERVER + ".vr-tmp"
open(tmp, "w", encoding="utf-8").write(patched)
try:
    py_compile.compile(tmp, doraise=True)
except py_compile.PyCompileError as e:
    os.remove(tmp); print("ABORT: won't parse; untouched.\n  %s" % str(e).splitlines()[-1][:150]); raise SystemExit(1)
bak = SERVER + ".bak-voiceroute-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy(SERVER, bak)
os.replace(tmp, SERVER)
print("PATCHED — removed the misplaced decorator. /api/voice/chat now hits the real voice_chat handler.")
print("  backup:", os.path.basename(bak))
print("  restart:  systemctl --user restart vintos-server   then re-run the test")
