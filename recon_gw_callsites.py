#!/usr/bin/env python3
"""recon_gw_callsites.py — Aegis, READ-ONLY, FAST. Show the call-site CONTEXT (±4 lines) for every
emotional_gravity_wells call in its importers, so the rebuilt module matches the real arg shapes: is record_visit
passed an embedding vector or an event dict? what is 'resonance'? what does apply_gravity's return feed? Nothing written."""
import os, re
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
CALLERS = ["emoclaw_utils.py", "latent_threads.py", "server.py", "subconscious_drift.py",
           "subconscious_context.py", "somatic-feedback.py"]
PAT = re.compile(r'emotional_gravity_wells|_gw_visit|_gw_load|_gw_ctx|_av_rv|\brecord_visit\b|\bapply_gravity\b|'
                 r'\bget_wells_context\b|\bload_wells\b')

for name in CALLERS:
    p = os.path.join(HIS, name)
    if not os.path.isfile(p): continue
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    marks = [i for i, l in enumerate(L) if PAT.search(l)]
    if not marks: continue
    print("\n===== %s =====" % name)
    shown = set()
    for i in marks:
        lo, hi = max(0, i - 4), min(len(L), i + 3)
        for j in range(lo, hi):
            if j in shown: continue
            shown.add(j)
            print("  %4d: %s" % (j + 1, L[j][:118]))
        print("   ---")

print("\n(READ-ONLY. Gives exact arg shapes to rebuild emotional_gravity_wells correctly.)")
