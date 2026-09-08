#!/usr/bin/env python3
"""dream_build_recon.py — READ-ONLY, capped. The exact pieces to build premonition-intersection dreams:
how self-prediction & gloria_prediction produce a next-state (call + output), latent_diffuser's
embed+mean-shift (to reuse over futures), and the dream-log seed format. Vintos side. Aegis."""
import os, re, json
HOME = os.path.expanduser("~")
TS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
def peek(p, pat, cap=16):
    if not os.path.isfile(p): print("  (missing)", p.replace(HOME,'~')); return
    print(f"-- {os.path.basename(p)} --"); n=0
    for i,l in enumerate(open(p,encoding='utf-8',errors='ignore').read().split("\n")):
        if re.search(pat,l,re.I) and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:4}| {l.strip()[:135]}"); n+=1
            if n>=cap: break

print("=== self-prediction.py (his next state: call + output) ===")
peek(os.path.join(TS,"self-prediction.py"), r'def |predict|next|state|dump|write|open\(|json|output|return|grok|api', 16)
print("\n=== gloria_prediction.py (her next state) ===")
peek(os.path.join(TS,"gloria_prediction.py"), r'def |predict|next|state|dump|write|open\(|json|output|return|grok|api', 16)
print("\n=== latent_diffuser.py — embed + mean-shift + write (to reuse over futures) ===")
peek(os.path.join(TS,"latent_diffuser.py"), r'def |embed|mean.?shift|mode|converge|weight|dump|seed_thread|dream|OUT|resolution', 20)

print("\n=== dream-log.json seed format (how a dream entry looks) ===")
p = os.path.join(MEM,"dream-log.json")
if os.path.isfile(p):
    try:
        d = json.load(open(p))
        items = d if isinstance(d,list) else (d.get("dreams") or list(d.values()))
        print("  entries:", len(items) if isinstance(items,list) else "?")
        if isinstance(items,list) and items:
            print("  keys:", list(items[-1].keys()) if isinstance(items[-1],dict) else type(items[-1]).__name__)
            print("  sample:", json.dumps(items[-1], ensure_ascii=True)[:280])
    except Exception as e: print("  (", e, ")")
else:
    print("  (no dream-log.json — checking who writes dreams)")
    import subprocess
    print(" ", subprocess.run(["bash","-lc", f"grep -rln 'dream-log.json' {TS} 2>/dev/null | grep -v pyc | head"], capture_output=True, text=True).stdout.replace(HOME,'~'))
