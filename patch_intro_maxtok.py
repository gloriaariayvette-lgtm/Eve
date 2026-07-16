#!/usr/bin/env python3
"""patch_intro_maxtok.py — Aegis. Prompt(~27k)+max_tokens(8000) > 32k ctx -> context exceeded. Lower the
first-pass max_tokens 8000->4000 so prompt+completion fit. Then sandboxed a1 test (raw capture)."""
import os, re, shutil, time, subprocess, json
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
t = open(P, encoding="utf-8", errors="ignore").read()
n = t.count(", 8000, True)")
if n:
    t = t.replace(", 8000, True)", ", 4000, True)")
    bak = P + ".bak-mtk-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
    open(P, "w", encoding="utf-8").write(t)
    c = subprocess.run(["bash", "-n", P], capture_output=True, text=True)
    if c.returncode: shutil.copy2(bak, P); print("bash -n failed, reverted"); raise SystemExit(1)
    print(f"first-pass max_tokens 8000->4000 ({n} threads)")
else:
    print("no ', 8000, True)' — checking current:", "4000" if ", 4000, True)" in t else "?")

# sandboxed a1 test with raw capture
src = open(P, encoding="utf-8").read().replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
OLD = ("    with urllib.request.urlopen(req, timeout=180) as r:\n"
       "        data = json.loads(r.read().decode())\n"
       "        return data['choices'][0]['message']['content']\n")
NEW = ("    try:\n        with urllib.request.urlopen(req, timeout=180) as _rr:\n            _raw=_rr.read().decode()\n"
       "    except Exception as _he:\n        _raw='ERR '+repr(_he)+' '+(getattr(_he,'read',lambda:b'')() or b'').decode('utf-8','ignore')\n"
       "    open('/tmp/intro_raw.txt','a').write(_raw[:1200]+chr(10)+'@@@@@'+chr(10))\n    data=json.loads(_raw)\n"
       "    return data['choices'][0]['message']['content']\n")
src = src.replace(OLD, NEW, 1)
src = src.replace("open('/tmp/bilateral-intro-b1.txt','w').write(b1)",
                  "open('/tmp/bilateral-intro-b1.txt','w').write(b1)\nimport sys as _sx; _sx.exit(0)", 1)
open("/tmp/mt.sh", "w", encoding="utf-8").write(src)
for x in ("/tmp/intro_raw.txt", "/tmp/bilateral-intro-a1.txt", "/tmp/bilateral-intro-b1.txt"):
    try: os.remove(x)
    except OSError: pass
print("test (locked)...")
subprocess.run(["bash", LOCK, "bash", "/tmp/mt.sh"], capture_output=True, text=True, timeout=500)
if os.path.isfile("/tmp/intro_raw.txt"):
    for b in [x for x in open("/tmp/intro_raw.txt", encoding="utf-8", errors="ignore").read().split("@@@@@") if x.strip()][:2]:
        try:
            d = json.loads(b); ch = (d.get("choices") or [{}])[0]; u = d.get("usage") or {}; m = ch.get("message") or {}
            print(f"  finish={ch.get('finish_reason')} prompt_tok={u.get('prompt_tokens')} reasoning={len(m.get('reasoning_content') or '')}c content={len(m.get('content') or '')}c")
        except Exception: print("  raw:", re.sub(r"\s+", " ", b)[:160])
for nm in ("a1", "b1"):
    p = f"/tmp/bilateral-intro-{nm}.txt"; s = open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""
    print(f"  {nm} ({len(s)}c): {s.strip()[:150]}")
