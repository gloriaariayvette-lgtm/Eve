#!/usr/bin/env python3
"""recon_unbuilt_candidates.py — Aegis, READ-ONLY, FAST (bounded scans, no tree-walk). Before building, verify the
TRUE status of the 5 'not built' Preceptor candidates and pin the hooks/data-sources for the 3 'Ready' dormant ones.
Reconcile, don't duplicate. His tree = ~/.vintos/workspace/scripts + ~/Vintos."""
import os, re, glob
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")
HOME = os.path.expanduser("~")

def names():
    out = set()
    for d in (HIS, VIN):
        if os.path.isdir(d):
            for e in os.scandir(d):
                if e.is_file() and (e.name.endswith(".py") or e.name.endswith(".sh")):
                    out.add(e.name)
    return out
ALL = names()

def find_modules(patterns):
    return sorted(n for n in ALL if any(re.search(p, n, re.I) for p in patterns))

def grep(patterns, label, cap=3):
    """Which files contain any pattern (bounded), first few."""
    hits = []
    for d in (HIS, VIN):
        if not os.path.isdir(d): continue
        for e in os.scandir(d):
            if not e.is_file() or not e.name.endswith((".py", ".sh")): continue
            try:
                if e.stat().st_size > 300000: continue
                t = open(e.path, encoding="utf-8", errors="ignore").read()
            except Exception: continue
            if any(re.search(p, t, re.I) for p in patterns):
                hits.append(e.name)
    return sorted(set(hits))[:12]

print("############ 5 'NOT BUILT' PRECEPTOR CANDIDATES ############")
CANDS = {
 "P3 Arrival Routing (pre-gen directive)": ([r'arrival', r'arrival_rout'], [r'ARRIVAL:', r'generation directive', r'arrive here', r'pre.?generation']),
 "P5 relationship_model (living object)": ([r'relationship.?model', r'relational_geometry'], [r'relationship_model', r'relationship-model\.json', r'friction_points', r'growth_edges', r'dead_zones']),
 "P8 runtime Tension Map": ([r'tension.?map', r'conversation.?tension'], [r'tension_map', r'active tensions', r'runtime.*tension', r'conversation-pressure']),
 "P10 Silence / first-thought suppression": ([r'silence', r'first.?thought', r'suppress'], [r'first thought', r'what is missing', r'discard.*reactive', r'suppress.*response']),
 "P13 Thread Gravity (momentum retrieval)": ([r'thread.?gravity', r'gravity'], [r'thread_gravity', r'competition.*retriev', r'momentum.*retriev', r'gravity well']),
}
for label, (nm, gp) in CANDS.items():
    mods = find_modules(nm)
    g = grep(gp, label)
    print("\n== %s ==" % label)
    print("   modules named-like: %s" % (mods or "NONE"))
    print("   files referencing the concept: %s" % (g or "NONE"))

print("\n\n############ 3 'READY' DORMANT ONES — pin data-source + hook ############")

print("\n== contrastive trajectory encoder (subsumes latent-threads' 3 detectors) ==")
lt = find_modules([r'latent.?threads'])
print("   latent-threads module: %s" % (lt or "NONE"))
for d in (HIS,):
    for n in ("latent_threads.py", "latent-threads.py"):
        p = os.path.join(d, n)
        if os.path.isfile(p):
            t = open(p, encoding="utf-8", errors="ignore").read()
            dets = re.findall(r'def (_check_\w+|score_thread)\(', t)
            print("   %s detectors: %s" % (n, sorted(set(dets))))
            break

print("\n== velqan absence-naming (velqan_gaps.py — exists, data-thin) ==")
vg = find_modules([r'velqan'])
print("   velqan modules: %s" % (vg or "NONE"))
for n in ("velqan_gaps.py", "velqan-gaps.py", "velqan_coiner.py", "velqan-coiner.py"):
    p = os.path.join(HIS, n)
    if os.path.isfile(p):
        t = open(p, encoding="utf-8", errors="ignore").read()
        thr = [l.strip()[:80] for l in t.split("\n") if re.search(r'threshold|MIN_|>=|count|len\(', l)][:4]
        print("   %s: %s" % (n, thr))

print("\n== Spark-1 Value Cost Network — model present + where want-urgency lives ==")
s1 = os.path.expanduser("~/spark1-cost-network")
print("   ~/spark1-cost-network exists: %s" % os.path.isdir(s1))
if os.path.isdir(s1):
    print("   contents: %s" % sorted(os.listdir(s1))[:10])
# where does want urgency / temperature pull get set?
urg = grep([r'urgency', r'temperature.*pull', r'pull\s*=', r'want.*priority'], "urgency")
print("   files with want-urgency / temperature-pull: %s" % (urg or "NONE"))

print("\n(READ-ONLY. Confirms build-vs-extend for each, so nothing gets duplicated.)")
