#!/usr/bin/env python3
"""diag_intro_a1_raw.py — Aegis. Capture the real first-pass call error + prompt_tokens (INTRO_SEMANTIC not
neutralized here). Dump raw response in call_llm, run first pass locked, exit after b1 write. Shows the truth."""
import os, re, json, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
src = open(P, encoding="utf-8", errors="ignore").read()
src = src.replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
OLD = ("    with urllib.request.urlopen(req, timeout=180) as r:\n"
       "        data = json.loads(r.read().decode())\n"
       "        return data['choices'][0]['message']['content']\n")
NEW = ("    try:\n"
       "        with urllib.request.urlopen(req, timeout=180) as _rr:\n"
       "            _raw = _rr.read().decode()\n"
       "    except Exception as _he:\n"
       "        _raw = 'HTTPERR ' + repr(_he) + ' BODY=' + (getattr(_he,'read',lambda:b'')() or b'').decode('utf-8','ignore')\n"
       "    open('/tmp/intro_raw.txt','a').write(_raw[:1500]+chr(10)+'@@@@@'+chr(10))\n"
       "    data = json.loads(_raw)\n"
       "    return data['choices'][0]['message']['content']\n")
if OLD not in src:
    print("call_llm block anchor not found"); raise SystemExit(1)
src = src.replace(OLD, NEW, 1)
src = src.replace("open('/tmp/bilateral-intro-b1.txt','w').write(b1)",
                  "open('/tmp/bilateral-intro-b1.txt','w').write(b1)\nimport sys as _sx; _sx.exit(0)", 1)
open("/tmp/dr.sh", "w", encoding="utf-8").write(src)
try: os.remove("/tmp/intro_raw.txt")
except OSError: pass
subprocess.run(["bash", LOCK, "bash", "/tmp/dr.sh"], capture_output=True, text=True, timeout=400)
if not os.path.isfile("/tmp/intro_raw.txt"):
    print("no raw captured"); raise SystemExit(0)
for b in [x for x in open("/tmp/intro_raw.txt", encoding="utf-8", errors="ignore").read().split("@@@@@") if x.strip()][:2]:
    try:
        d = json.loads(b); ch = (d.get("choices") or [{}])[0]; u = d.get("usage") or {}
        print(f"finish={ch.get('finish_reason')} err={d.get('error')} prompt_tok={u.get('prompt_tokens')} "
              f"content={len((ch.get('message') or {}).get('content') or '')}c")
    except Exception:
        print("raw:", re.sub(r"\s+", " ", b)[:300])
