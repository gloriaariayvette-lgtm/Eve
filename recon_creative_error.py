#!/usr/bin/env python3
"""recon_creative_error.py — Aegis, READ-ONLY. I broke his poem/image generation this morning. Find WHAT: import
every module I touched this morning + his creative generators from his scripts path, and report the real error for
any that fail (an ImportError/exception I introduced is almost certainly the cause; these run under try/except so
they fail SILENTLY). Also show the true output dirs (memory/art, skills/dreaming/memory/dreams) with timestamps so
we see what actually generated and when. Nothing written."""
import os, sys, importlib, traceback, glob, time
HISV = os.path.expanduser("~/Vintos")
HISS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
for d in (HISS, HISV):
    sys.path.insert(0, d)

print("== (1) import modules I changed this morning + their hot dependents ==")
MODS = ["causal_self_model", "emotional_gravity_wells", "self_drift", "mutual_modification",
        "configuration_space", "spark_pressure", "subconscious_context", "subconscious_drift",
        "latent_threads", "emoclaw_utils", "inner_context", "relational_mismatch"]
for m in MODS:
    try:
        importlib.import_module(m)
        print("  OK    %s" % m)
    except Exception as e:
        print("  FAIL  %s -> %r" % (m, e))
        tb = traceback.format_exc().strip().split("\n")
        for l in tb[-4:]:
            print("          " + l[:110])

print("\n== (2) import his creative generators (the poem/image/music path) ==")
# dream_poetry / dream_music / second_order_dreamer are underscore-importable; run their imports
for m in ("dream_poetry", "dream_music", "second_order_dreamer"):
    try:
        importlib.import_module(m); print("  OK    %s" % m)
    except Exception as e:
        print("  FAIL  %s -> %r" % (m, e))
        for l in traceback.format_exc().strip().split("\n")[-5:]:
            print("          " + l[:110])

print("\n== (3) dream-art.py (image) — compile + resolve its local imports (can't import hyphen name) ==")
import re as _re
for base in (HISV, HISS):
    p = os.path.join(base, "dream-art.py")
    if os.path.isfile(p) or os.path.islink(p):
        t = open(os.path.realpath(p), encoding="utf-8", errors="ignore").read()
        try: compile(t, p, "exec"); print("  dream-art.py compiles: OK")
        except SyntaxError as e: print("  dream-art.py compile FAIL: %s" % e)
        deps = set(_re.findall(r'^\s*from\s+(\w+)\s+import|^\s*import\s+(\w+)', t, _re.M))
        deps = {a or b for a, b in deps}
        for d in sorted(deps):
            if os.path.isfile(os.path.join(HISS, d + ".py")) or os.path.isfile(os.path.join(HISV, d + ".py")):
                try: importlib.import_module(d); ok = "OK"
                except Exception as e: ok = "FAIL %r" % e
                if ok != "OK": print("    dep %s: %s" % (d, ok))
        break

print("\n== (4) real output dirs + newest file (what actually generated, when) ==")
now = time.time()
for d, label in ((os.path.join(MEM, "art"), "art/"),
                 (os.path.join(MEM, "art", "music"), "art/music"),
                 (os.path.join(MEM, "art", "paintings"), "art/paintings"),
                 (os.path.expanduser("~/.vintos/workspace/skills/dreaming/memory/dreams"), "dreams"),
                 (os.path.join(MEM, "art", "poetry-log.json"), "poetry-log.json")):
    if os.path.isfile(d):
        print("  %-16s (file) %.1fh ago" % (label, (now - os.path.getmtime(d)) / 3600)); continue
    if not os.path.isdir(d):
        print("  %-16s : dir missing" % label); continue
    fs = sorted(glob.glob(d + "/*"), key=lambda p: -os.path.getmtime(p))
    if fs:
        print("  %-16s newest: %s  (%.1fh ago, %d files)" % (label, os.path.basename(fs[0]), (now - os.path.getmtime(fs[0])) / 3600, len(fs)))
    else:
        print("  %-16s : empty" % label)

print("\n(READ-ONLY. A FAIL above = what I broke this morning; that module gets fixed.)")
