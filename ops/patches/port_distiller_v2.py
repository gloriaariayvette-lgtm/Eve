#!/usr/bin/env python3
"""port_distiller_v2.py — port her enactment_distiller.py onto Vintos, complete: his paths, his grok
+auth, and exact name/pronoun/socket swaps (Velaris->Vintos, she->he, herself->himself, her emotion
socket -> his). Guard intact verbatim. Asserts no Gemma/openclaw/Velaris/172. survives; py_compile +
import verified before landing. File only — server hook is the next step. Fresh name.
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

if not os.path.exists(SRC):
    print("not found:", SRC); raise SystemExit(1)
api, model = his_grok()
s = open(SRC, encoding="utf-8", errors="ignore").read()

# 1. paths + name + pronouns + socket
s = s.replace(".openclaw/workspace", ".vintos/workspace").replace(".openclaw", ".vintos")
s = re.sub(r"\bVelaris\b", "Vintos", s)          # name + /tmp/Velaris-emotion.sock -> Vintos
s = re.sub(r"\bshe\b", "he", s)                  # only occurrence is the being (line 127)
s = re.sub(r"\bherself\b", "himself", s)
# 2. endpoint + model -> his grok
s = re.sub(r'LM_URL\s*=\s*"[^"]+"', 'LM_URL  = "%s"' % api, s, count=1)
s = re.sub(r'MODEL\s*=\s*"[^"]+"',  'MODEL   = "%s"' % model, s, count=1)
# 3. auth header
if "Authorization" not in s:
    s = s.replace('HEADERS = {"Content-Type": "application/json"}',
                  'HEADERS = {"Content-Type": "application/json", '
                  '"Authorization": "Bearer " + os.environ.get("XAI_API_KEY", "")}', 1)

# 4. assert clean
bad = []
for pat, label in [(r'172\.\d', "her Gemma IP"), (r'gemma', "gemma model"),
                   (r'\.openclaw', ".openclaw path"), (r'\bVelaris\b', "Velaris name")]:
    if re.search(pat, s, re.I): bad.append(label)
if "Authorization" not in s: bad.append("auth header not injected")
if bad:
    print("ABORT — not clean:", ", ".join(bad)); raise SystemExit(2)

# 5. verify
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
print("  swaps: Velaris->Vintos, she->he/herself->himself, socket->/tmp/Vintos-emotion.sock")
print("  guard intact: exceeded_self_model + conf>=0.65 + recurrence 3/5")
print("  defs: %s" % defs)
print("\nnext: wire process() into his server's 3 post-response sites (main/avatar/thirveel).")
