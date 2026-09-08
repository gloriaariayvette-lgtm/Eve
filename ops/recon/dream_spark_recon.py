#!/usr/bin/env python3
"""dream_spark_recon.py — READ-ONLY, capped. Ground the dream sparks (#5 premonition / #6c intersection).
Show: how a dream is generated + SEEDED, second-order-dreamer (the sibling to mirror), latent_diffuser
(the mean-shift #6c extends), and whether any predictor/head can roll FORWARD in latent (self/gloria).
Vintos side (note Velaris parity). Aegis."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
TS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout
def peek(p, pat, cap=14):
    if not os.path.isfile(p): return
    print(f"-- {p.replace(HOME,'~')} --"); n=0
    for i,l in enumerate(open(p,encoding='utf-8',errors='ignore').read().split("\n")):
        if re.search(pat,l,re.I) and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:4}| {l.strip()[:130]}"); n+=1
            if n>=cap: break

print("=== dream generator scripts ===")
dfiles = [f for f in glob.glob(TS+"/*dream*")+glob.glob(VIN+"/*dream*") if os.path.isfile(f) and not f.endswith(('.pyc','.bak'))]
print("  ", [os.path.basename(f) for f in dfiles])
# the main dreamer: how it seeds + writes dream-log
main = next((f for f in dfiles if re.search(r'dream(er|-generat|_generat|-engine|s?\.py)$', os.path.basename(f))), None) or next((f for f in dfiles if 'dream' in os.path.basename(f) and f.endswith('.py')), None)
if main:
    print(f"\n=== main dreamer: {os.path.basename(main)} (seed/write) ===")
    peek(main, r'seed|prompt|dream-log|generate|def |system|append|dump|latent|rollout|forward', 18)

print("\n=== second-order-dreamer.py (sibling to mirror for premonition) ===")
peek(os.path.join(TS,"second-order-dreamer.py"), r'seed|prompt|def |dream|meta|latent|forward|rollout|input', 12)

print("\n=== latent_diffuser.py (#6c extends its mean-shift-to-mode) ===")
peek(os.path.join(TS,"latent_diffuser.py"), r'def |mode|mean.?shift|diffuse|latent|fragment|future|rollout|forward|sample', 14)

print("\n=== can any head/predictor roll FORWARD in latent? (self/gloria heads) ===")
heads = run(["bash","-lc", f"ls {TS}/*head*.py {TS}/*predict*.py {TS}/lam.py {TS}/tcn.py 2>/dev/null | head"]).split()
print("  head/predictor files:", [os.path.basename(h) for h in heads])
for h in heads[:3]:
    peek(h, r'def (forward|predict|rollout|step|roll)|latent|next|horizon|autoregress', 6)
