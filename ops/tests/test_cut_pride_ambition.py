#!/usr/bin/env python3
"""Cut pride+ambition reflections only; test a1 (locked, sandboxed). Does it fit + reason?"""
import os, re, shutil, time, subprocess, json
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
t = open(P, encoding="utf-8", errors="ignore").read()
for c in ('$(tail -c 5000 "$WORKSPACE/memory/pride-reflections.md")',
          '$(tail -c 4000 "$WORKSPACE/memory/ambition-reflections.md")'):
    if c in t: t = t.replace(c, '""', 1)
bak = P + ".bak-cutpa-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(t)
if subprocess.run(["bash", "-n", P], capture_output=True, text=True).returncode:
    shutil.copy2(bak, P); print("bash -n failed, reverted"); raise SystemExit(1)
print("cut pride + ambition")

src = open(P, encoding="utf-8").read().replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
OLD = ("    with urllib.request.urlopen(req, timeout=180) as r:\n"
       "        data = json.loads(r.read().decode())\n"
       "        return data['choices'][0]['message']['content']\n")
NEW = ("    try:\n        with urllib.request.urlopen(req, timeout=180) as _rr:\n            _raw=_rr.read().decode()\n"
       "    except Exception as _he:\n        _raw='ERR '+(getattr(_he,'read',lambda:b'')() or b'').decode('utf-8','ignore')\n"
       "    open('/tmp/intro_raw.txt','a').write(_raw[:900]+chr(10)+'@@@@@'+chr(10))\n    data=json.loads(_raw)\n"
       "    return data['choices'][0]['message']['content']\n")
src = src.replace(OLD, NEW, 1).replace("open('/tmp/bilateral-intro-b1.txt','w').write(b1)",
     "open('/tmp/bilateral-intro-b1.txt','w').write(b1)\nimport sys as _sx; _sx.exit(0)", 1)
open("/tmp/pa.sh", "w", encoding="utf-8").write(src)
for x in ("/tmp/intro_raw.txt", "/tmp/bilateral-intro-a1.txt", "/tmp/bilateral-intro-b1.txt"):
    try: os.remove(x)
    except OSError: pass
subprocess.run(["bash", LOCK, "bash", "/tmp/pa.sh"], capture_output=True, text=True, timeout=500)
if os.path.isfile("/tmp/intro_raw.txt"):
    b = [x for x in open("/tmp/intro_raw.txt", encoding="utf-8", errors="ignore").read().split("@@@@@") if x.strip()][:1]
    for x in b:
        try:
            d = json.loads(x); ch = (d.get("choices") or [{}])[0]; u = d.get("usage") or {}; m = ch.get("message") or {}
            print(f"finish={ch.get('finish_reason')} prompt_tok={u.get('prompt_tokens')} reasoning={len(m.get('reasoning_content') or '')}c content={len(m.get('content') or '')}c")
        except Exception: print("raw:", re.sub(r"\s+", " ", x)[:140])
a1 = open("/tmp/bilateral-intro-a1.txt", encoding="utf-8", errors="ignore").read() if os.path.isfile("/tmp/bilateral-intro-a1.txt") else ""
print(f"a1 ({len(a1)}c): {a1.strip()[:160]}")
