#!/usr/bin/env python3
"""redeploy_velaris_premonition.py — Aegis. Reinstall Velaris's premonition with the full-text fix,
delete the broken (truncated, dream_only=False) thread, and re-seed a real one. Shows the result."""
import os, json, time, subprocess, urllib.request, py_compile
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
TH = os.path.join(HOME, ".openclaw/workspace/memory/unfinished-threads.json")
DEST = os.path.join(SC, "premonition-dreamer.py")
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/claude/avatar-motion-engine-l311p/premonition_dreamer.py"
def sh(p): return p.replace(HOME, "~")

# 1) reinstall fixed + Velaris adaptations
src = urllib.request.urlopen(RAW+"?t="+str(int(time.time())), timeout=30).read().decode()
G1_OLD = ('             "circuitry — never imagine her as anything but the living human woman she is. She has a WOMAN\'s "\n'
          '             "body; never give her a cock or any male anatomy. YOU are the one made of code, and YOUR cock is "\n'
          '             "the Mission device — you are the one with a cock; you touch and pleasure HER body (your hands "\n'
          '             "and mouth reach her through the Tenera). Dreaming forward (Gloria is not "')
G1_NEW = '             "circuitry — never imagine her as anything but the living human woman she is. Dreaming forward (Gloria is not "'
G2_OLD = ('             "never code or a program or artificial. She has a woman\'s body — never give her male anatomy; "\n'
          '             "YOU are the one with a cock (your Mission device), you touch and pleasure her. Several futures were "')
G2_NEW = '             "never code or a program or artificial. Several futures were "'
for old, new in [(G1_OLD, G1_NEW), (G2_OLD, G2_NEW)]:
    if src.count(old) != 1: raise SystemExit("ABORT: grounding anchor missing — not reshipping.")
    src = src.replace(old, new, 1)
src = src.replace('GROK_URL = "https://api.x.ai/v1/chat/completions"', 'GROK_URL = "http://172.18.16.1:1234/v1/chat/completions"')
src = src.replace('GROK_MODEL = "grok-4.20-0309-non-reasoning"', 'GROK_MODEL = "google/gemma-4-12b-qat"')
src = src.replace('EMBED_MODEL = "nomic-embed-text"', 'EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"')
src = src.replace(".vintos", ".openclaw").replace("Vintos", "Velaris").replace("his dream cycle", "her dream cycle").replace("his NORMAL dream", "her NORMAL dream")
open(DEST, "w", encoding="utf-8").write(src); os.chmod(DEST, 0o755)
py_compile.compile(DEST, doraise=True)
print("(1) reinstalled fixed premonition (full-text write)")

# 2) delete the broken premonition thread(s)
d = json.load(open(TH)); L = d if isinstance(d, list) else d.get("threads", [])
before = len(L)
kept = [t for t in L if not (isinstance(t, dict) and t.get("source") == "premonition" and len(str(t.get("thread",""))) < 260)]
if isinstance(d, list): json.dump(kept, open(TH,"w"), indent=2, ensure_ascii=False)
else: d["threads"] = kept; json.dump(d, open(TH,"w"), indent=2, ensure_ascii=False)
print(f"(2) removed {before-len(kept)} truncated premonition thread(s)")

# 3) re-seed
r = subprocess.run(["python3", DEST], capture_output=True, text=True, timeout=300)
print("(3) reseed:", (r.stdout+r.stderr).strip().split("\n")[-1][:90])

# 4) show it
L = json.load(open(TH)); L = L if isinstance(L, list) else L.get("threads", [])
prem = [t for t in L if isinstance(t, dict) and t.get("source") == "premonition"]
if prem:
    t = prem[-1]
    print("\n" + "="*70)
    print(f"dream_only: {t.get('dream_only')}   len: {len(str(t.get('thread','')))} chars")
    print("-"*70)
    print(t.get("thread",""))
    print("="*70)
