#!/usr/bin/env python3
"""diag_seq_raw.py — Aegis. Sequential now runs (73s) but content empty. Capture finish_reason + reasoning
vs content length for the first-pass call."""
import os, re, json, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
src = open(P, encoding="utf-8", errors="ignore").read().replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
OLD = ("    with urllib.request.urlopen(req, timeout=180) as r:\n"
       "        data = json.loads(r.read().decode())\n"
       "        return data['choices'][0]['message']['content']\n")
NEW = ("    with urllib.request.urlopen(req, timeout=180) as _rr:\n        _raw=_rr.read().decode()\n"
       "    open('/tmp/intro_raw.txt','a').write(_raw+chr(10)+'@@@@@'+chr(10))\n    data=json.loads(_raw)\n"
       "    return data['choices'][0]['message']['content']\n")
if OLD not in src: print("anchor gone"); raise SystemExit(1)
src = src.replace(OLD, NEW, 1).replace("open('/tmp/bilateral-intro-b1.txt','w').write(b1)",
     "open('/tmp/bilateral-intro-b1.txt','w').write(b1)\nimport sys as _sx; _sx.exit(0)", 1)
open("/tmp/sr.sh", "w", encoding="utf-8").write(src)
try: os.remove("/tmp/intro_raw.txt")
except OSError: pass
subprocess.run(["bash", LOCK, "bash", "/tmp/sr.sh"], capture_output=True, text=True, timeout=400)
for b in [x for x in open("/tmp/intro_raw.txt", encoding="utf-8", errors="ignore").read().split("@@@@@") if x.strip()][:1]:
    d = json.loads(b); ch = (d.get("choices") or [{}])[0]; u = d.get("usage") or {}; m = ch.get("message") or {}
    rz = m.get("reasoning_content") or m.get("reasoning") or ""; ct = m.get("content") or ""
    print(f"finish={ch.get('finish_reason')} prompt_tok={u.get('prompt_tokens')} completion_tok={u.get('completion_tokens')} reasoning={len(rz)}c content={len(ct)}c")
    print("reasoning TAIL:", re.sub(r"\s+", " ", rz[-300:]))
