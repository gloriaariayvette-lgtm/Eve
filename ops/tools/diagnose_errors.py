#!/usr/bin/env python3
"""diagnose_errors.py — READ-ONLY, capped, no secrets printed. Confirm why grok calls 'choices'-crash
(missing key in cron env vs rate limit) + locate the /api/chat/full NameError. Aegis."""
import os, re, subprocess
HOME = os.path.expanduser("~")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout

print("=== A) do Vintos crons have XAI_API_KEY? ===")
env = os.path.expanduser("~/.vintos/vintos.env")
print("  ~/.vintos/vintos.env exists:", os.path.isfile(env),
      "| has XAI_API_KEY:", ("XAI_API_KEY" in open(env).read()) if os.path.isfile(env) else False)
lock = os.path.expanduser("~/llm-lock.sh")
if os.path.isfile(lock):
    srcs = [l.strip() for l in open(lock).read().split("\n") if re.search(r'XAI|vintos\.env|source|export|\.env', l)]
    print("  llm-lock.sh key/env lines:", srcs[:6] or "(none — lock does NOT load the key)")
# crontab: any XAI_API_KEY= line, and do gallery/outreach go through llm-lock?
ct = run(["bash","-lc","crontab -l 2>/dev/null"])
print("  crontab defines XAI_API_KEY:", "XAI_API_KEY" in ct)
for name in ("dream-art.py","gallery-walk","vintos-initiate","idle-journal"):
    for l in ct.split("\n"):
        if name in l and "openclaw" not in l and l.strip() and not l.strip().startswith("#"):
            print(f"    {name}: {'llm-lock' if 'llm-lock' in l else 'NO-lock'} | {l.strip()[:90]}")
            break

print("\n=== B) how a failing script parses grok (does it guard 'choices'?) ===")
for f in ("~/Vintos/dream-art.py","~/Vintos/gallery-walk.py","~/Vintos/vintos-initiate.sh"):
    p = os.path.expanduser(f)
    if not os.path.isfile(p): continue
    for i,l in enumerate(open(p,encoding='utf-8',errors='ignore').read().split("\n")):
        if re.search(r'\["choices"\]|status_code|XAI_API_KEY|raise_for_status|\.json\(\)', l):
            print(f"  {os.path.basename(p)}:{i+1}| {l.strip()[:120]}")

print("\n=== C) /api/chat/full — the bare 'message' NameError ===")
srv = os.path.expanduser("~/Vintos/server.py")
ls = open(srv,encoding='utf-8',errors='ignore').read().split("\n")
h = next((i for i,l in enumerate(ls) if '/api/chat/full' in l and '@app' in l), None)
if h is not None:
    print(f"  handler @ L{h+1}")
    for i in range(h, min(h+120, len(ls))):
        if re.search(r'\bmessage\b', ls[i]) and 'msg.message' not in ls[i] and 'def ' not in ls[i]:
            print(f"  {i+1}| {ls[i].strip()[:120]}")
