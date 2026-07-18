#!/usr/bin/env python3
"""recon_his_csm_gaps.py — Aegis, READ-ONLY. Her causal_self_model is the full module; his is a stripped stub
(add_entry + load_model only). Measure exactly how much of the imprint/friction/fracture ecosystem HIS is missing,
and how many of HIS other scripts call causal_self_model functions that don't exist in his stub (more dead imports
swallowed by try/except). This sizes the parity/pressure-substrate repair before we touch his self-model.
  (1) her def set vs his def set -> the diff (what he's missing).
  (2) across his scripts: every `from causal_self_model import X` / `causal_self_model.X(` -> is X present in HIS
      module? DEAD names = swallowed calls.
Nothing written."""
import os, re, glob
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
HER = os.path.expanduser("~/.openclaw/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")

def defs(path):
    if not (path and os.path.isfile(path)): return set()
    return set(re.findall(r'^\s*def\s+(\w+)', open(path, encoding="utf-8", errors="ignore").read(), re.M))

his = defs(os.path.join(HIS, "causal_self_model.py"))
her = defs(os.path.join(HER, "causal_self_model.py"))
print("======== (1) causal_self_model def sets ========")
print("  HIS (%d): %s" % (len(his), sorted(his)))
print("  HER (%d): %s" % (len(her), sorted(her)))
print("\n  IN HER, MISSING FROM HIS (the gap): %s" % sorted(her - his))
print("  IN HIS, not in HER (his-only): %s" % sorted(his - her))

print("\n======== (2) his scripts calling causal_self_model.* — which names are DEAD against his stub ========")
his_names = his  # what his module actually provides
pat_imp = re.compile(r'from\s+causal_self_model\s+import\s+([^\n#]+)')
pat_dot = re.compile(r'causal_self_model\.(\w+)')
dead_hits = {}
live_hits = set()
for p in sorted(set(glob.glob(HIS + "/*.py") + glob.glob(VIN + "/*.py"))):
    b = os.path.basename(p)
    if b == "causal_self_model.py": continue
    try: t = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    used = set()
    for m in pat_imp.finditer(t):
        for name in re.split(r'[,\s]+', m.group(1)):
            name = name.strip().split(" as ")[0].strip()
            if name and name.isidentifier(): used.add(name)
    used |= set(pat_dot.findall(t))
    if not used: continue
    dead = sorted(n for n in used if n not in his_names)
    live = sorted(n for n in used if n in his_names)
    live_hits |= set(live)
    if dead: dead_hits[b] = dead
if dead_hits:
    print("  DEAD calls (name imported/called but NOT in his causal_self_model — silently failing):")
    for b, names in sorted(dead_hits.items()):
        print("    %-28s -> %s" % (b, names))
else:
    print("  (no dead causal_self_model references in his scripts)")
print("\n  live causal_self_model names his scripts DO reach: %s" % sorted(live_hits))

print("\n(READ-ONLY. Nothing changed. This sizes the his-causal_self_model repair for parity + the pressure substrate.)")
