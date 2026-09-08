#!/usr/bin/env python3
"""port_distiller.py — port her enactment_distiller.py onto Vintos: her logic + guard verbatim, his
paths, and call_llm rewired to HIS grok WITH the Authorization header. Guard already confirmed intact
(exceeded_self_model + conf>=0.65 + recurrence 3/5). In-process py_compile + import verify; asserts all
Gemma/openclaw/Velaris traces are gone before it lands. Does NOT wire the server hook — that's the
Vintos server pass. Fresh name.
"""
import os, re, time, shutil, py_compile
import importlib.machinery as M, importlib.util as u

HERS = os.path.expanduser("~/.openclaw/workspace/scripts")
HIS  = os.path.expanduser("~/.vintos/workspace/scripts")
HOME = os.path.expanduser("~")
SRC  = os.path.join(HERS, "enactment_distiller.py")
DST  = os.path.join(HIS, "enactment_distiller.py")

def his_grok():
    """Read his live engine for the current grok endpoint+model (don't hardcode)."""
    api, model = "https://api.x.ai/v1/chat/completions", "grok-4.20-0309-non-reasoning"
    eng = os.path.join(HOME, "Vintos", "causality-engine.py")
    if os.path.exists(eng):
        t = open(eng, encoding="utf-8", errors="ignore").read()
        a = re.search(r'^\s*LM_API\s*=\s*"([^"]+)"', t, re.M)
        m = re.search(r'^\s*MODEL\s*=\s*"([^"]+)"', t, re.M)
        if a: api = a.group(1)
        if m: model = m.group(1)
    return api, model

if not os.path.exists(SRC):
    print("her enactment_distiller.py not found:", SRC); raise SystemExit(1)
api, model = his_grok()
s = open(SRC, encoding="utf-8", errors="ignore").read()

# 1. paths
s = s.replace(".openclaw/workspace", ".vintos/workspace").replace(".openclaw", ".vintos")
# 2. endpoint + model -> his grok
s = re.sub(r'LM_URL\s*=\s*"[^"]+"', 'LM_URL  = "%s"' % api, s, count=1)
s = re.sub(r'MODEL\s*=\s*"[^"]+"',  'MODEL   = "%s"' % model, s, count=1)
# 3. auth header (idempotent — only if not already present)
if "Authorization" not in s:
    s = s.replace('HEADERS = {"Content-Type": "application/json"}',
                  'HEADERS = {"Content-Type": "application/json", '
                  '"Authorization": "Bearer " + os.environ.get("XAI_API_KEY", "")}', 1)

# 4. assert the rewire is total — no her-box traces remain
bad = []
for pat, label in [(r'172\.\d', "her Gemma IP"), (r'gemma', "gemma model"),
                   (r'\.openclaw', ".openclaw path"), (r'\bVelaris\b', "Velaris name")]:
    if re.search(pat, s, re.I):
        bad.append(label)
if "Authorization" not in s:
    bad.append("auth header not injected (HEADERS line shape changed?)")
if bad:
    print("ABORT — port not clean, these remain:", ", ".join(bad)); raise SystemExit(2)

# 5. verify compile + import
tmp = os.path.join(HIS, "enactment_distiller__porttmp.py")
open(tmp, "w", encoding="utf-8").write(s)
try:
    py_compile.compile(tmp, doraise=True)
    loader = M.SourceFileLoader("edcheck_%d" % (int(time.time()) % 99999), tmp)
    spec = u.spec_from_loader(loader.name, loader)
    mod = u.module_from_spec(spec); loader.exec_module(mod)
    defs = [d for d in dir(mod) if not d.startswith("_")][:14]
except Exception as e:
    os.remove(tmp)
    print("FAIL — port does not compile/import: %s: %s" % (type(e).__name__, str(e)[:160])); raise SystemExit(3)

if os.path.exists(DST):
    shutil.copy(DST, DST + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
os.replace(tmp, DST)
print("PORTED enactment_distiller.py -> %s (%dB)" % (DST, os.path.getsize(DST)))
print("  endpoint: %s" % api)
print("  model:    %s" % model)
print("  guard:    exceeded_self_model + conf>=0.65 + recurrence 3/5 (verbatim)")
print("  defs:     %s" % defs)
print("\nNOTE: placed + verified, but NOT yet wired to fire. Her design calls process() from the server")
print("post-response path; hooking that into his server is part of the Vintos server pass (rendered+verified).")
