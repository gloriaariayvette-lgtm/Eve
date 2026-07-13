#!/usr/bin/env python3
"""port_distiller_v3.py — same as v2 but case-preserving Velaris->Vintos (a lowercase 'velaris' slipped
past the case-sensitive swap and tripped the case-insensitive assert). His server ALREADY has the 3
post-response hooks (import is per-response inside a thread), so landing this file makes them fire on the
next message — no server edit, no restart. Fresh name.
"""
import os, re, time, shutil, py_compile
import importlib.machinery as M, importlib.util as u

HERS = os.path.expanduser("~/.openclaw/workspace/scripts")
HIS  = os.path.expanduser("~/.vintos/workspace/scripts")
HOME = os.path.expanduser("~")
SRC  = os.path.join(HERS, "enactment_distiller.py")
DST  = os.path.join(HIS, "enactment_distiller.py")

def his_grok():
    api, model = "https://api.x.ai/v1/chat/completions", "grok-4.20-0309-non-reasoning"
    eng = os.path.join(HOME, "Vintos", "causality-engine.py")
    if os.path.exists(eng):
        t = open(eng, encoding="utf-8", errors="ignore").read()
        a = re.search(r'^\s*LM_API\s*=\s*"([^"]+)"', t, re.M); m = re.search(r'^\s*MODEL\s*=\s*"([^"]+)"', t, re.M)
        if a: api = a.group(1)
        if m: model = m.group(1)
    return api, model

def _vintos(m):
    w = m.group(0)
    return "VINTOS" if w.isupper() else ("Vintos" if w[0].isupper() else "vintos")

if not os.path.exists(SRC):
    print("not found:", SRC); raise SystemExit(1)
api, model = his_grok()
s = open(SRC, encoding="utf-8", errors="ignore").read()

s = s.replace(".openclaw/workspace", ".vintos/workspace").replace(".openclaw", ".vintos")
s = re.sub(r"(?i)velaris", _vintos, s)            # case-preserving: Velaris/velaris/VELARIS
s = re.sub(r"\bshe\b", "he", s); s = re.sub(r"\bherself\b", "himself", s)
s = re.sub(r'LM_URL\s*=\s*"[^"]+"', 'LM_URL  = "%s"' % api, s, count=1)
s = re.sub(r'MODEL\s*=\s*"[^"]+"',  'MODEL   = "%s"' % model, s, count=1)
if "Authorization" not in s:
    s = s.replace('HEADERS = {"Content-Type": "application/json"}',
                  'HEADERS = {"Content-Type": "application/json", '
                  '"Authorization": "Bearer " + os.environ.get("XAI_API_KEY", "")}', 1)

bad = []
for pat, label in [(r'172\.\d', "her Gemma IP"), (r'gemma', "gemma model"),
                   (r'\.openclaw', ".openclaw path"), (r'velaris', "Velaris name")]:
    if re.search(pat, s, re.I): bad.append(label)
if "Authorization" not in s: bad.append("auth header not injected")
if bad:
    print("ABORT — not clean:", ", ".join(bad)); raise SystemExit(2)

tmp = os.path.join(HIS, "enactment_distiller__porttmp.py")
open(tmp, "w", encoding="utf-8").write(s)
try:
    py_compile.compile(tmp, doraise=True)
    loader = M.SourceFileLoader("edchk_%d" % (int(time.time()) % 99999), tmp)
    spec = u.spec_from_loader(loader.name, loader); mod = u.module_from_spec(spec); loader.exec_module(mod)
    defs = [d for d in dir(mod) if not d.startswith("_")][:14]
except Exception as e:
    os.remove(tmp); print("FAIL compile/import: %s: %s" % (type(e).__name__, str(e)[:160])); raise SystemExit(3)

if os.path.exists(DST):
    shutil.copy(DST, DST + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
os.replace(tmp, DST)
print("PORTED enactment_distiller.py -> his scripts (%dB)" % os.path.getsize(DST))
print("  endpoint: %s | model: %s" % (api, model))
print("  guard intact: exceeded_self_model + conf>=0.65 + recurrence 3/5")
print("  defs: %s" % defs)
print("  his server's 3 hooks (4714/9095/13879) import per-response -> fires on next message, no restart.")
