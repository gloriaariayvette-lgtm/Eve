#!/usr/bin/env python3
"""dream_input_recon.py — READ-ONLY, capped. Re-plumb premonition through the NORMAL dream cycle:
what does the main dreamer read as its seed (threads? preoccupation?), how does seed_thread store a
thread, and does the dreamer note the source TYPE (so an 'imagined possibility' marker can ride into
the dream)? Vintos side. Aegis."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
TS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout
def peek(p, pat, cap=16):
    if not os.path.isfile(p): print("  (missing)", p.replace(HOME,'~')); return
    print(f"-- {os.path.basename(p)} --"); n=0
    for i,l in enumerate(open(p,encoding='utf-8',errors='ignore').read().split("\n")):
        if re.search(pat,l,re.I) and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:4}| {l.strip()[:135]}"); n+=1
            if n>=cap: break

print("=== the dream scripts (which is the main 'normal' dreamer?) ===")
dfiles = sorted(set(f for f in glob.glob(TS+"/*dream*.sh")+glob.glob(VIN+"/*dream*.sh")+glob.glob(TS+"/preoccupation*")+glob.glob(VIN+"/preoccupation*") if os.path.isfile(f) and not f.endswith('.bak')))
print("  ", [os.path.basename(f) for f in dfiles])
# who writes dream-log.json (the dreamer)?
w = run(["bash","-lc", f"grep -rln 'dream-log.json' {TS} {VIN} 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head"]).split()
print("  writes dream-log.json:", [os.path.basename(x) for x in w])

print("\n=== the main dreamer: what does it read as its SEED? ===")
main = next((f for f in dfiles if re.search(r'^dream\.sh|^dream-architecture|preoccupation-dream', os.path.basename(f))), dfiles[0] if dfiles else None)
for f in (dfiles[:3]):
    peek(f, r'thread|preoccup|unfinished|seed|prompt|PROMPT|read|cat |latent|input|source|type', 12)

print("\n=== seed_thread: thread format + where threads live ===")
peek(os.path.join(TS,"emoclaw_utils.py"), r'def seed_thread|unfinished-threads|thread.*=|kind|source|dump.*thread|append', 12)
print("\n  a current thread entry (shape):")
import json
for fn in ("unfinished-threads.json",):
    p=os.path.expanduser("~/.vintos/workspace/memory/"+fn)
    if os.path.isfile(p):
        try:
            o=json.load(open(p)); items=o if isinstance(o,list) else (o.get("threads") or list(o.values()))
            if items: print("   keys:", list(items[-1].keys()) if isinstance(items[-1],dict) else "?", "|", json.dumps(items[-1],ensure_ascii=True)[:200])
        except Exception as e: print("   (",e,")")

print("\n=== does the dreamer carry a source/type note into the dream prompt? ===")
if main:
    peek(main, r'invented|not real|symbolic|imagined|source|type|note|reality', 8)
