#!/usr/bin/env python3
"""cut_capabilities_test.py — Aegis. Content lands but prompt (24.4k) leaves tight reasoning room -> flaky.
Cut CAPABILITIES (~3.8k tok) to journal-size the prompt, then test a1/b1 with raw capture."""
import os, re, shutil, time, subprocess, json
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
t = open(P, encoding="utf-8", errors="ignore").read()
c = '$(cat "$WORKSPACE/memory/CAPABILITIES.md")'
if c in t: t = t.replace(c, '""', 1); print("cut CAPABILITIES")
else: print("CAPABILITIES anchor not found (maybe already cut)")
bak = P + ".bak-cutcap-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(t)
if subprocess.run(["bash", "-n", P], capture_output=True, text=True).returncode:
    shutil.copy2(bak, P); print("bash -n failed, reverted"); raise SystemExit(1)

src = open(P, encoding="utf-8").read().replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
OLD = ("    with urllib.request.urlopen(req, timeout=180) as r:\n"
       "        data = json.loads(r.read().decode())\n"
       "        return data['choices'][0]['message']['content']\n")
NEW = ("    with urllib.request.urlopen(req, timeout=180) as _rr:\n        _raw=_rr.read().decode()\n"
       "    open('/tmp/intro_raw.txt','a').write(_raw+chr(10)+'@@@@@'+chr(10))\n    data=json.loads(_raw)\n"
       "    return data['choices'][0]['message']['content']\n")
src = src.replace(OLD, NEW, 1).replace("open('/tmp/bilateral-intro-b1.txt','w').write(b1)",
     "open('/tmp/bilateral-intro-b1.txt','w').write(b1)\nimport sys as _sx; _sx.exit(0)", 1)
open("/tmp/cc.sh", "w", encoding="utf-8").write(src)
for x in ("/tmp/intro_raw.txt", "/tmp/bilateral-intro-a1.txt", "/tmp/bilateral-intro-b1.txt"):
    try: os.remove(x)
    except OSError: pass
print("test (locked)..."); t0 = time.time()
subprocess.run(["bash", LOCK, "bash", "/tmp/cc.sh"], capture_output=True, text=True, timeout=600)
print(f"done {int(time.time()-t0)}s")
raws = [x for x in open("/tmp/intro_raw.txt", encoding="utf-8", errors="ignore").read().split("@@@@@") if x.strip()] if os.path.isfile("/tmp/intro_raw.txt") else []
for i, b in enumerate(raws[:2]):
    try:
        d = json.loads(b); ch = (d.get("choices") or [{}])[0]; u = d.get("usage") or {}; m = ch.get("message") or {}
        print(f"  call{i+1}: finish={ch.get('finish_reason')} prompt_tok={u.get('prompt_tokens')} reasoning={len(m.get('reasoning_content') or '')}c content={len(m.get('content') or '')}c")
    except Exception: print("  raw:", re.sub(r"\s+", " ", b)[:120])
for nm in ("a1", "b1"):
    p = f"/tmp/bilateral-intro-{nm}.txt"; s = open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""
    print(f"{nm} ({len(s)}c): {s.strip()[:160]}")
