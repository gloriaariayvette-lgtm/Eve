#!/usr/bin/env python3
"""recon_6b.py — Aegis, READ-ONLY, capped. Spark 6b: give the latent a TEMPERATURE — not just WHERE he
is but HOW SETTLED that belief is (certainty + temp). Consumers: dreams seek heat, mirrors seek
instability, pearls seek cooling. Map: (1) where beliefs/latent state live + their schema, (2) whether
any certainty/temperature notion already exists, (3) the dream / mirror / pearl consumers to wire."""
import os, re, glob, json, subprocess
HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".vintos/workspace")
MEM = os.path.join(WS, "memory")
SC = os.path.join(WS, "scripts")
def sh(p): return p.replace(HOME, "~")

print("=== (1) belief / latent state stores + schema ===")
for name in ("belief-sediment.json", "frame-state.json", "causal-self-model.json",
             "narrative-identity.json", "yearning-scars.json", "self-model-latent.json", "latent-state.json"):
    p = os.path.join(MEM, name)
    if not os.path.isfile(p):
        continue
    try:
        obj = json.load(open(p))
    except Exception as e:
        print(f"  {name}: (unreadable {e})"); continue
    sample = obj[0] if isinstance(obj, list) and obj else (obj if isinstance(obj, dict) else None)
    keys = list(sample.keys()) if isinstance(sample, dict) else f"({type(obj).__name__})"
    n = len(obj) if isinstance(obj, (list, dict)) else 1
    print(f"  {name:26} n={n:<4} keys/first-entry: {keys}")

print("\n=== (2) does any certainty / temperature / settled notion already exist? ===")
hits = subprocess.run(["bash","-lc",
    f"grep -rilE 'temperature|certainty|\\bsettled\\b|conviction|\\bheat\\b|phase.?transition|volatil' "
    f"{SC} {MEM} 2>/dev/null | grep -viE '\\.pyc|\\.bak|node_modules' | head -12"],
    capture_output=True, text=True).stdout.strip()
print("  " + (hits.replace(HOME,'~').replace(chr(10),'\n  ') or "(none — 6b introduces it)"))

print("\n=== (3) the consumers to wire ===")
groups = {
    "DREAMS (seek heat)":   ["*dream*", "should-dream*", "preoccupation*", "latent_diffuser*", "latent-diffuser*"],
    "MIRRORS (seek instability)": ["*mirror*"],
    "PEARLS (seek cooling)": ["*pearl*"],
}
for label, pats in groups.items():
    files = sorted({f for pat in pats for base in (SC, WS, MEM) for f in glob.glob(os.path.join(base, pat)) if os.path.isfile(f)})
    print(f"  -- {label} --")
    if not files:
        print("     (none found)")
    for f in files[:5]:
        # show how it currently SELECTS what to work on (the hook point for temp-weighting)
        sel = ""
        for l in open(f, encoding="utf-8", errors="ignore").read().split("\n"):
            if re.search(r'sort|score|select|choose|random|pick|salien|momentum|weight|max\(|top', l) and l.strip() and not l.strip().startswith("#"):
                sel = l.strip()[:96]; break
        print(f"     {sh(f):58} {('sel: '+sel) if sel else ''}")

print("\n=== belief-sediment sample entry (the natural home for certainty+temp) ===")
p = os.path.join(MEM, "belief-sediment.json")
if os.path.isfile(p):
    try:
        obj = json.load(open(p))
        e = obj[0] if isinstance(obj, list) and obj else obj
        print("  " + json.dumps(e, ensure_ascii=False)[:300])
    except Exception as ex:
        print("  (unreadable)", ex)

print("\n=== where the latent 'position' is computed (self/gloria prediction heads) ===")
for name in ("self-prediction.py", "gloria_prediction.py", "living_trajectory.py", "latent-threads.py"):
    for base in (SC, WS):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            print(f"  {sh(p)} ({os.path.getsize(p)}B)"); break
