#!/usr/bin/env python3
"""recon_gravity_wells.py — Aegis, READ-ONLY, FAST. emotional_gravity_wells.py is 1 line but imported by 6 core
files (like the causal_self_model stub was). Recover the EXPECTED API so it can be rebuilt correctly:
  (1) the actual 1-line content (+ any .bak with real content).
  (2) every name each importer calls from it (from emotional_gravity_wells import X / .X(  ) — the API to satisfy.
  (3) live LIVE-import test: does `import emotional_gravity_wells; hasattr(...)` currently fail/return nothing?
  (4) any gravity/well json + what related modules (latent_threads) expect back (shape).
His tree = ~/.vintos/workspace/scripts. Nothing written."""
import os, re, sys, glob, importlib
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")

egw = os.path.join(HIS, "emotional_gravity_wells.py")
print("== (1) current content of emotional_gravity_wells.py ==")
if os.path.isfile(egw):
    print("   %r" % open(egw, encoding="utf-8", errors="ignore").read()[:300])
print("   backups:")
for b in sorted(glob.glob(egw + ".bak*") + glob.glob(os.path.join(HIS, "emotional-gravity-wells.py*"))):
    sz = os.path.getsize(b)
    print("      %s (%d bytes)%s" % (os.path.basename(b), sz, "  <-- has content!" if sz > 200 else ""))

print("\n== (2) API the importers expect (from emotional_gravity_wells import X / egw.X(...)) ==")
callers = ["emoclaw_utils.py", "latent_threads.py", "latent-threads.py", "merged_full_route.py",
           "server.py", "somatic-feedback.py", "somatic_feedback.py", "subconscious_context.py", "subconscious_drift.py"]
api = set()
for name in callers:
    p = os.path.join(HIS, name)
    if not os.path.isfile(p): continue
    t = open(p, encoding="utf-8", errors="ignore").read()
    imports = re.findall(r'from\s+emotional_gravity_wells\s+import\s+([^\n#]+)', t)
    dotted = re.findall(r'emotional_gravity_wells\.(\w+)', t)
    aliased = re.findall(r'import\s+emotional_gravity_wells\s+as\s+(\w+)', t)
    local = set()
    for grp in imports:
        for nm in re.split(r'[,\s]+', grp):
            nm = nm.strip().split(" as ")[0].strip()
            if nm and nm.isidentifier(): local.add(nm)
    # if aliased, find alias.X(
    for al in aliased:
        local |= set(re.findall(r'%s\.(\w+)' % re.escape(al), t))
    local |= set(dotted)
    if local:
        print("   %-26s calls: %s" % (name, sorted(local)))
        api |= local
        # show a couple call sites with args, to infer signatures
        for nm in sorted(local)[:3]:
            for l in t.split("\n"):
                if re.search(r'\b%s\s*\(' % re.escape(nm), l):
                    print("        e.g. %s" % l.strip()[:96]); break
print("\n   => API to satisfy: %s" % sorted(api))

print("\n== (3) live import test ==")
sys.path.insert(0, HIS)
try:
    m = importlib.import_module("emotional_gravity_wells")
    print("   import OK. present names: %s" % [n for n in dir(m) if not n.startswith("__")][:20])
    for nm in sorted(api):
        print("      hasattr %s: %s" % (nm, hasattr(m, nm)))
except Exception as e:
    print("   import FAILED: %r" % e)

print("\n== (4) related json / expected shape ==")
for fn in ("gravity-wells.json", "emotional-gravity-wells.json", "emotional-gravity.json", "gravity.json"):
    p = os.path.join(MEM, fn)
    if os.path.isfile(p): print("   %s (%d bytes)" % (fn, os.path.getsize(p)))

print("\n(READ-ONLY. Recovers the gravity-wells API so the 1-line stub can be rebuilt to satisfy its 6 importers.)")
