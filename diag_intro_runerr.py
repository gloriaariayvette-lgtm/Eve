#!/usr/bin/env python3
"""diag_intro_runerr.py — Aegis. The first-pass call_llm errors fast and run() swallows it. Make run print
the exception + dump the raw HTTP response/error, run first pass (locked), show what actually failed."""
import os, re, subprocess, time
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
src = open(P, encoding="utf-8", errors="ignore").read()
src = src.replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
# print the swallowed exception
src = src.replace("        results[i] = None\n",
                  "        results[i] = None\n        import sys as _es; print('RUNERR', repr(e), file=_es.stderr, flush=True)\n", 1)
# dump raw response/error inside call_llm
src = src.replace(
    "    with urllib.request.urlopen(req, timeout=180) as r:\n        data = json.loads(r.read().decode())\n",
    "    try:\n        with urllib.request.urlopen(req, timeout=180) as _rr:\n            _raw = _rr.read().decode()\n"
    "    except Exception as _he:\n        _raw = 'HTTPERR ' + repr(_he) + ' BODY=' + (getattr(_he,'read',lambda:b'')() or b'').decode('utf-8','ignore')\n"
    "    open('/tmp/intro_call.txt','a').write(_raw[:1200]+chr(10)+'@@@@@'+chr(10))\n    data = json.loads(_raw)\n", 1)
open("/tmp/di.sh", "w", encoding="utf-8").write(src)
try: os.remove("/tmp/intro_call.txt")
except OSError: pass
print("running first pass (locked)...")
t0 = time.time(); r = subprocess.run(["bash", LOCK, "bash", "/tmp/di.sh"], capture_output=True, text=True, timeout=400)
print(f"done {int(time.time()-t0)}s")
print("STDERR:", (r.stderr.strip()[-300:] or "(none)"))
if os.path.isfile("/tmp/intro_call.txt"):
    blk = open("/tmp/intro_call.txt", encoding="utf-8", errors="ignore").read().split("@@@@@")[0]
    print("RAW:", re.sub(r"\s+", " ", blk)[:400])
