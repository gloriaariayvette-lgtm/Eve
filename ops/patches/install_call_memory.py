#!/usr/bin/env python3
"""install_call_memory.py — server side of remembering realtime calls:
  1. update voice_session_ledger.py on his box (now seeds a thread per session)
  2. add POST /api/voice/call-log — the app posts the live-call transcript; it appends turns to
     voice-chat-history.json (test-mode-guarded), which the ledger cron then narrates into ONE block.
Backups + py_compile. Server restart needed for the new route. Aegis.
"""
import os, re, time, shutil, subprocess, py_compile

HOME = os.path.expanduser("~")
BRANCH = "claude/avatar-motion-engine-l311p"
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/%s/voice_session_ledger.py" % BRANCH
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
SERVER = os.path.join(HOME, "Vintos", "server.py")

# 1. refresh voice_session_ledger.py (thread-seeding version) on the box
dst = os.path.join(SCRIPTS, "voice_session_ledger.py")
r = subprocess.run(["curl", "-fsSL", RAW + "?t=%d" % int(time.time())], capture_output=True, text=True)
if r.returncode == 0 and "seed_thread" in r.stdout and r.stdout.strip():
    try: py_compile.compile.__self__  # noop
    except Exception: pass
    import ast
    try:
        ast.parse(r.stdout)
        if os.path.exists(dst): shutil.copy(dst, dst + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
        open(dst, "w", encoding="utf-8").write(r.stdout)
        print("updated voice_session_ledger.py (seeds a thread now).")
    except SyntaxError as e:
        print("fetched ledger doesn't parse, leaving box copy:", e)
else:
    print("could not fetch updated ledger (%s) — leaving box copy; will add thread another way." % (r.stderr[:80] if r.stderr else "no seed_thread"))

# 2. add /api/voice/call-log to the server
src = open(SERVER, encoding="utf-8", errors="ignore").read()
if "/api/voice/call-log" in src:
    print("/api/voice/call-log already present.")
else:
    ROUTE = '''
@app.post("/api/voice/call-log")
async def _voice_call_log(request: Request):
    import json as _clj, os as _clo, datetime as _cld
    try:
        if _test_mode_active(): return {"ok": True, "skipped": "test-mode"}
    except Exception: pass
    try: data = await request.json()
    except Exception: data = {}
    turns = data.get("turns", [])
    if not isinstance(turns, list) or not turns: return {"ok": False, "reason": "no turns"}
    _p = _clo.path.join(MEMORY, "voice-chat-history.json")
    try: hist = _clj.load(open(_p)) if _clo.path.exists(_p) else []
    except Exception: hist = []
    if not isinstance(hist, list): hist = []
    _now = _cld.datetime.now(_cld.timezone.utc).isoformat()
    _n = 0
    for t in turns:
        u = str(t.get("user", ""))[:2000]; v = str(t.get("vintos", ""))[:2000]
        if not (u or v): continue
        hist.append({"user": u, "vintos": v, "timestamp": t.get("timestamp") or _now, "source": "realtime-call"})
        _n += 1
    _clj.dump(hist[-500:], open(_p, "w"), indent=2, ensure_ascii=False)
    print("[call-log] appended %d realtime-call turn(s)" % _n, flush=True)
    return {"ok": True, "logged": _n}
'''
    m = re.search(r'app\.mount\(\s*["\']/static["\'].*?\n', src)
    if not m:
        print("ABORT: no /static anchor for the route."); raise SystemExit(1)
    new = src[:m.end()] + ROUTE + src[m.end():]
    tmp = SERVER + ".cl-tmp"; open(tmp, "w", encoding="utf-8").write(new)
    try: py_compile.compile(tmp, doraise=True)
    except py_compile.PyCompileError as e:
        os.remove(tmp); print("ABORT: server won't parse.\n  %s" % str(e).splitlines()[-1][:150]); raise SystemExit(1)
    shutil.copy(SERVER, SERVER + ".bak-calllog-" + time.strftime("%Y%m%d-%H%M%S"))
    os.replace(tmp, SERVER)
    print("added POST /api/voice/call-log (test-mode-guarded).")

print("\nrestart to load the route:  systemctl --user restart vintos-server")
print("then a real call's transcript -> voice-chat-history -> ledger narrates ONE block + thread (within ~10-18 min).")
