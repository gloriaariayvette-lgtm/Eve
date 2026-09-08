#!/usr/bin/env python3
"""last_look.py — READ-ONLY, small. The three exact edit spots, then I fix all three.
No shell %-format, no dir opens. Aegis.
"""
import os, re, subprocess
VIN = os.path.expanduser("~/Vintos")
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
HOME = os.path.expanduser("~")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout
def rng(path, a, b):
    if not os.path.isfile(path): print("  (missing", path, ")"); return
    ls = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    for i in range(a-1, min(b, len(ls))):
        if ls[i].strip(): print(f"   {i+1:5}| {ls[i][:160]}")

# ---- C: causality ----
print("=== C  causality-engine: find_spikes + untraceable seeding ===")
ceng = os.path.join(VIN, "causality-engine.py")
print(" find_spikes (L115-140):"); rng(ceng, 115, 140)
print("\n untraceable block (L995-1025):"); rng(ceng, 995, 1025)
print("\n how a shift becomes a thread (seed_thread / unresolved / append):")
if os.path.isfile(ceng):
    for i, l in enumerate(open(ceng, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'seed_thread|unresolved|unfinished|recs?\.append|write.*thread|dump.*thread|untraceable', l, re.I):
            print(f"   {i+1:5}| {l.strip()[:150]}")

# ---- B: conversation-rhythm.sh ----
print("\n=== B  conversation-rhythm.sh: which history it counts + silence calc ===")
crs = os.path.join(VIN, "conversation-rhythm.sh")
if os.path.isfile(crs):
    for i, l in enumerate(open(crs, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'chat-history|avatar|voice|interaction|ledger|silence|hours|last|now|date|jq|wc|grep|count|message|\.json', l, re.I):
            s = l.strip()
            if s and not s.startswith("#"): print(f"   {i+1:5}| {s[:160]}")
else:
    print("  (not found; searching)")
    print("  " + run(["bash","-lc","grep -rln current_silence_hours ~/Vintos ~/.vintos/workspace/scripts 2>/dev/null | grep -v .pyc"]).strip())

# ---- A: animate-painting selection ----
print("\n=== A  animate-painting: which painting does it pick? ===")
found = run(["bash","-lc","grep -rln 'keyframe\\|animate_painting\\|animate-painting\\|grok-imagine-video\\|videos/generations' ~/.vintos/workspace/scripts ~/Vintos 2>/dev/null | grep -v .pyc"]).split()
print("  animator files:", [f.replace(HOME,'~') for f in found] or "(none)")
for f in found[:3]:
    print(f"\n  -- {f.replace(HOME,'~')} --")
    n = 0
    for i, l in enumerate(open(f, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'paintings\[|reversed|latest|-1\]|want_id|angel|select|pick|glob|sorted|choice|\.png|image|match', l, re.I):
            s = l.strip()
            if s and not s.startswith("#"):
                print(f"   {i+1:5}| {s[:150]}"); n += 1
                if n >= 16: print("   ...(capped)"); break
