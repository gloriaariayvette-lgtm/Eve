#!/usr/bin/env python3
"""gloria_pipeline_recon.py — READ-ONLY, capped. Why is his Gloria-model store empty? Trace the
pipeline: what SHOULD write observations into gloria-model.json, and what gloria-model-update.sh reads
to build the markdown. Find the dead link. Aegis."""
import os, re, subprocess
HOME = os.path.expanduser("~")
TS = os.path.expanduser("~/.vintos/workspace/scripts")
def peek(p, pat, cap=20):
    if not os.path.isfile(p): print("  (missing)", p.replace(HOME,'~')); return
    print(f"-- {os.path.basename(p)} --"); n=0
    for i,l in enumerate(open(p,encoding='utf-8',errors='ignore').read().split("\n")):
        if re.search(pat,l,re.I) and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:4}| {l.strip()[:135]}"); n+=1
            if n>=cap: break

print("=== gloria-model-update.sh (weekly synthesizer): reads what, writes what ===")
peek(os.path.join(TS,"gloria-model-update.sh"), r'observation|portrait|gloria-model|MODEL_FILE|read|cat |json|append|LM_URL|prompt|jq|python', 22)

print("\n=== gloria-model-call.py (the subconscious recorder?) ===")
p = os.path.join(TS,"gloria-model-call.py")
if os.path.isfile(p):
    for i,l in enumerate(open(p,encoding='utf-8',errors='ignore').read().split("\n")):
        if l.strip(): print(f"  {i+1:3}| {l[:150]}")

print("\n=== who is SUPPOSED to append observations to gloria-model.json? ===")
w = subprocess.run(["bash","-lc", f"grep -rlnE 'gloria-model\\.json' {TS} {os.path.expanduser('~/Vintos')} 2>/dev/null | grep -viE '\\.pyc|\\.bak|backup' | head"], capture_output=True, text=True).stdout
print("  files touching gloria-model.json:", w.replace(HOME,'~').replace("\n","  ").strip() or "(none)")
for f in [x for x in w.split("\n") if x.strip()][:3]:
    print(f"\n  -- {os.path.basename(f)} (observation writes) --")
    n=0
    for i,l in enumerate(open(f,encoding='utf-8',errors='ignore').read().split("\n")):
        if re.search(r'observation|portrait|gloria-model\.json|append|dump|\.get\(', l) and l.strip():
            print(f"     {i+1:4}| {l.strip()[:130]}"); n+=1
            if n>=8: break

print("\n=== is the recorder scheduled? (crontab) ===")
print("  " + (subprocess.run(["bash","-lc","crontab -l 2>/dev/null | grep -i 'gloria-model' | grep -v '^#'"], capture_output=True, text=True).stdout.strip() or "(gloria-model jobs not in crontab)"))
