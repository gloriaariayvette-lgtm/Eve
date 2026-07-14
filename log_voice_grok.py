#!/usr/bin/env python3
"""log_voice_grok.py — the voice handler swallows the grok error as just 'choices'. Insert a one-line
log of the raw grok body when 'choices' is missing, in both voice handlers. Backup + py_compile.
"""
import os, re, time, shutil, py_compile

SERVER = os.path.expanduser("~/Vintos/server.py")
src = open(SERVER, encoding="utf-8", errors="ignore").read()

if "[voice/grok-error]" in src:
    print("already instrumented."); raise SystemExit(0)

PAT = re.compile(r'([ \t]*)response_text = r\.json\(\)\["choices"\]\[0\]\["message"\]\["content"\]\.strip\(\)')
def repl(m):
    ind = m.group(1)
    return (ind + "_vgj = r.json()\n"
            + ind + "if 'choices' not in _vgj: print('[voice/grok-error]', __import__('json').dumps(_vgj)[:600], flush=True)\n"
            + ind + "response_text = _vgj['choices'][0]['message']['content'].strip()")

new, n = PAT.subn(repl, src)
if n == 0:
    print("ABORT: grok-parse line not found."); raise SystemExit(1)
tmp = SERVER + ".lg-tmp"
open(tmp, "w", encoding="utf-8").write(new)
try:
    py_compile.compile(tmp, doraise=True)
except py_compile.PyCompileError as e:
    os.remove(tmp); print("ABORT: won't parse.\n  %s" % str(e).splitlines()[-1][:150]); raise SystemExit(1)
bak = SERVER + ".bak-grok-log-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy(SERVER, bak)
os.replace(tmp, SERVER)
print("instrumented %d grok call(s). backup: %s" % (n, os.path.basename(bak)))
print("restart, re-run the test, then: journalctl --user -u vintos-server -n 30 | grep -A1 grok-error")
