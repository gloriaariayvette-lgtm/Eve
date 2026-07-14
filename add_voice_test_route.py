#!/usr/bin/env python3
"""add_voice_test_route.py — add a real GET /voice-test route to the live server that serves the
generated Lux test page (memory/voice/voice-test.html). So it's reachable at http://<aegis>:8500/voice-test
instead of guessing a static path. Idempotent; backup; py_compile.
"""
import os, re, time, shutil, py_compile

SERVER = os.path.expanduser("~/Vintos/server.py")
src = open(SERVER, encoding="utf-8", errors="ignore").read()
if '/voice-test' in src:
    print("already present — GET /voice-test route exists."); raise SystemExit(0)

ROUTE = '''
@app.get("/voice-test")
async def _voice_test_page():
    from fastapi.responses import HTMLResponse
    import os as _vto
    _p = _vto.path.expanduser("~/.vintos/workspace/memory/voice/voice-test.html")
    if _vto.path.exists(_p):
        return HTMLResponse(open(_p, encoding="utf-8").read())
    return HTMLResponse("<body style='font-family:system-ui;background:#111;color:#eee'>"
                        "<h2>No voice test yet</h2><p>Run test_voice_full_v3.py, then reload.</p></body>")
'''

# insert right after the first StaticFiles /static mount (app is defined + mounts done there)
m = re.search(r'app\.mount\(\s*["\']/static["\'].*?\n', src)
if m:
    idx = m.end()
    new = src[:idx] + ROUTE + src[idx:]
else:
    # fallback: after `app = FastAPI(...)`
    m2 = re.search(r'app\s*=\s*FastAPI\([^\n]*\)\n', src)
    if not m2:
        print("ABORT: no mount or FastAPI() anchor found."); raise SystemExit(1)
    new = src[:m2.end()] + ROUTE + src[m2.end():]

tmp = SERVER + ".vtroute-tmp"
open(tmp, "w", encoding="utf-8").write(new)
try:
    py_compile.compile(tmp, doraise=True)
except py_compile.PyCompileError as e:
    os.remove(tmp); print("ABORT: won't parse.\n  %s" % str(e).splitlines()[-1][:150]); raise SystemExit(1)
bak = SERVER + ".bak-vtroute-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy(SERVER, bak)
os.replace(tmp, SERVER)
print("added GET /voice-test  (backup: %s)" % os.path.basename(bak))
print("restart, then open  http://<your-aegis-tailscale-host>:8500/voice-test  on your phone.")
