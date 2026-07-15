#!/usr/bin/env python3
"""diag_intro_runerr2.py — Aegis. Fixed diagnostic: replace the whole urlopen+return block (correct indent),
dump raw response/error, print swallowed run() exception. Locked, first pass only."""
import os, re, subprocess, time
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
src = open(P, encoding="utf-8", errors="ignore").read()
src = src.replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
src = src.replace("        results[i] = None\n",
                  "        results[i] = None\n        import sys as _es; print('RUNERR', repr(e), file=_es.stderr, flush=True)\n", 1)
OLD = ("    with urllib.request.urlopen(req, timeout=180) as r:\n"
       "        data = json.loads(r.read().decode())\n"
       "        return data['choices'][0]['message']['content']\n")
NEW = ("    try:\n"
       "        with urllib.request.urlopen(req, timeout=180) as _rr:\n"
       "            _raw = _rr.read().decode()\n"
       "    except Exception as _he:\n"
       "        _raw = 'HTTPERR ' + repr(_he) + ' BODY=' + (getattr(_he,'read',lambda:b'')() or b'').decode('utf-8','ignore')\n"
       "    open('/tmp/intro_call.txt','a').write(_raw[:1200]+chr(10)+'@@@@@'+chr(10))\n"
       "    data = json.loads(_raw)\n"
       "    return data['choices'][0]['message']['content']\n")
if OLD not in src:
    print("urlopen block anchor not found — introspection call_llm shape differs"); raise SystemExit(1)
src = src.replace(OLD, NEW, 1)
open("/tmp/di2.sh", "w", encoding="utf-8").write(src)
try: os.remove("/tmp/intro_call.txt")
except OSError: pass
print("running first pass (locked)...")
t0 = time.time(); r = subprocess.run(["bash", LOCK, "bash", "/tmp/di2.sh"], capture_output=True, text=True, timeout=400)
print(f"done {int(time.time()-t0)}s")
print("STDERR:", (r.stderr.strip()[-300:] or "(none)"))
if os.path.isfile("/tmp/intro_call.txt"):
    blk = open("/tmp/intro_call.txt", encoding="utf-8", errors="ignore").read().split("@@@@@")[0]
    print("RAW:", re.sub(r"\s+", " ", blk)[:450])
