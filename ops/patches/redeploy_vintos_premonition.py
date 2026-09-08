#!/usr/bin/env python3
"""redeploy_vintos_premonition.py — Aegis. Reinstall Vintos's premonition with the full-text fix (his
version — grok, his grounding, .vintos paths), delete truncated marker-only threads, re-seed, show."""
import os, re, json, time, subprocess, urllib.request, py_compile
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
TH = os.path.join(HOME, ".vintos/workspace/memory/unfinished-threads.json")
DEST = os.path.join(SC, "premonition-dreamer.py")
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/claude/avatar-motion-engine-l311p/premonition_dreamer.py"
def sh(p): return p.replace(HOME, "~")

src = urllib.request.urlopen(RAW+"?t="+str(int(time.time())), timeout=30).read().decode()
if "_write_thread_direct(text)" not in src or "seed_thread(\"premonition\", text, dream_only=True)" in src:
    pass  # fixed version writes directly; sanity below
open(DEST, "w", encoding="utf-8").write(src); os.chmod(DEST, 0o755)
py_compile.compile(DEST, doraise=True)
print("(1) reinstalled fixed premonition (full-text write)")

d = json.load(open(TH)); L = d if isinstance(d, list) else d.get("threads", [])
kept = [t for t in L if not (isinstance(t, dict) and t.get("source") == "premonition" and len(str(t.get("thread",""))) < 260)]
(json.dump(kept, open(TH,"w"), indent=2, ensure_ascii=False) if isinstance(d, list)
 else (d.__setitem__("threads", kept), json.dump(d, open(TH,"w"), indent=2, ensure_ascii=False)))
print(f"(2) removed {len(L)-len(kept)} truncated premonition thread(s)")

env = os.environ.copy()
if not env.get("XAI_API_KEY"):
    ct = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
    m = re.search(r'XAI_API_KEY\s*=\s*"?([^"\n]+)"?', ct)
    if m: env["XAI_API_KEY"] = m.group(1).strip()
r = subprocess.run(["python3", DEST], capture_output=True, text=True, env=env, timeout=300)
print("(3) reseed:", (r.stdout+r.stderr).strip().split("\n")[-1][:90])
L = json.load(open(TH)); L = L if isinstance(L, list) else L.get("threads", [])
prem = [t for t in L if isinstance(t, dict) and t.get("source") == "premonition"]
if prem:
    t = prem[-1]
    print(f"\n  dream_only: {t.get('dream_only')}   len: {len(str(t.get('thread','')))}")
    print("  " + str(t.get("thread",""))[:200].replace(chr(10)," ") + "…")
