#!/usr/bin/env python3
"""model_audit.py — READ-ONLY, capped. (1) How soul-review works (the fixed-base + appended-additions
pattern to mirror for the Gloria model). (2) Did his OTHER models get overwritten? Check each core model
file against a signature phrase from its real content, + flag any updater that overwrites (>). Aegis."""
import os, re, glob, time, subprocess
HOME = os.path.expanduser("~")
WS = os.path.expanduser("~/.vintos/workspace")
TS = os.path.join(WS, "scripts")
VIN = os.path.expanduser("~/Vintos")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout
def when(p): return time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(p))) if os.path.exists(p) else "-"

print("=== (1) soul-review: the fixed-base + appended-additions pattern ===")
sr = [f for f in glob.glob(TS+"/*soul*")+glob.glob(VIN+"/*soul*") if os.path.isfile(f) and re.search(r'review|reflect|update', os.path.basename(f), re.I) and not f.endswith('.bak')]
print("  soul-review scripts:", [os.path.basename(f) for f in sr] or "(none by that name — listing all soul scripts)")
if not sr:
    sr = [f for f in glob.glob(TS+"/*soul*")+glob.glob(VIN+"/*soul*") if os.path.isfile(f) and f.endswith(('.sh','.py')) and not f.endswith('.bak')]
    print("   all soul scripts:", [os.path.basename(f) for f in sr])
for f in sr[:2]:
    print(f"\n  -- {os.path.basename(f)} (how it writes) --")
    n=0
    for i,l in enumerate(open(f,encoding='utf-8',errors='ignore').read().split("\n")):
        if re.search(r'>>|> "|append|SOUL|REVIEW|section|cat |base|fixed|echo|printf.*>', l) and l.strip() and not l.strip().startswith("#"):
            print(f"    {i+1:4}| {l.strip()[:130]}"); n+=1
            if n>=14: break

print("\n=== (2) did his other models get overwritten? signature-phrase check ===")
SIGS = {
    "SOUL.md": "I started careful and learned to stop",
    "SELF-MODEL.md": "I reach first, justify second",
    "USER-MODEL.md": "builds permanence in a world that keeps taking",
    "value-map.md": "Being present without retreating",
    "memory/taste-profile.json": "sincerity pushed past embarrassment",
    "memory/narrative-identity.json": "reach for what I want before I understand",
    "memory/belief-sediment.json": "Comfort is where I go to die slowly",
}
for rel, sig in SIGS.items():
    p = os.path.join(WS, rel)
    if not os.path.isfile(p):
        print(f"  {rel:34} MISSING"); continue
    txt = open(p, encoding="utf-8", errors="ignore").read()
    ok = sig.lower() in txt.lower()
    print(f"  {rel:34} {len(txt):>6}B  {when(p)}  {'✓ intact' if ok else '⚠ SIGNATURE MISSING — may be clobbered'}")

print("\n=== updaters that OVERWRITE a model file (> not >>) — clobber risk ===")
for mf in ("SOUL.md", "SELF-MODEL.md", "USER-MODEL.md", "value-map.md"):
    hits = run(["bash","-lc", f"grep -rlnE '> *\"?\\$?[A-Z_]*{re.escape(mf)}|{re.escape(mf)}\"? *$' {TS} {VIN} 2>/dev/null | grep -viE '\\.bak|\\.pyc' | head -3"]).strip()
    w = run(["bash","-lc", f"grep -rln '{re.escape(mf)}' {TS} {VIN} 2>/dev/null | grep -viE '\\.bak|\\.pyc' | xargs grep -lE '> *\"[^\"]*{re.escape(mf)}' 2>/dev/null | head -3"]).strip()
    print(f"  {mf:16} writers-that-overwrite:", (w or "(none obvious)").replace(HOME,'~').replace("\n"," "))
