#!/usr/bin/env python3
"""recon_config_ground.py — Aegis, READ-ONLY, FAST (one flat scripts dir, size-capped, single pass — no tree-walk).
Ground the step-#3 build:
  (1) does any configuration-space / eve_possible / attractor / basin scaffolding already exist?
  (2) the nomic encoder / embedding entry point the JEPA already uses (to reuse for window embeddings).
  (3) idle-journal reflection surface (for the 'fold vs own cron' ritual-placement choice).
Prints filenames + token line numbers only (bounded). Nothing written."""
import os, re
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")

TOK = re.compile(r'eve_possible|configuration.?space|\battractor|\bbasin\b|reachable|held_by|neither_yet', re.I)
EMB = re.compile(r'nomic|def embed|def encode|sentence.?transformer|get_embedding|\.encode\(|jepa.*encode|encoder', re.I)

def scan(dirpath, rx, label):
    print("\n== %s (in %s) ==" % (label, dirpath))
    if not os.path.isdir(dirpath): print("  (dir missing)"); return
    hits = 0
    for e in sorted(os.scandir(dirpath), key=lambda x: x.name):
        if not e.is_file() or not e.name.endswith(".py"): continue
        try:
            if e.stat().st_size > 300000: continue
            t = open(e.path, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        ls = [str(i + 1) for i, l in enumerate(t.split("\n")) if rx.search(l)]
        if ls:
            hits += 1
            print("  %-30s : %s%s" % (e.name, ",".join(ls[:10]), " …" if len(ls) > 10 else ""))
    if not hits: print("  (no matches)")

scan(HIS, TOK, "(1) configuration/attractor scaffolding")
scan(HIS, EMB, "(2) embedding / nomic encoder entry points")

print("\n== (2b) likely encoder module — show the callable signature ==")
for name in ("jepa_encoder.py", "jepa_predictor.py", "nomic_encoder.py", "embeddings.py", "encoder.py"):
    p = os.path.join(HIS, name)
    if os.path.isfile(p):
        for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
            if re.search(r'def (embed|encode|get_embedding)\w*\(|nomic|model\s*=.*[Ee]mbed', l):
                print("  %s:%d: %s" % (name, i + 1, l.strip()[:96]))

print("\n== (3) memory: any existing config/attractor json ==")
if os.path.isdir(MEM):
    for e in sorted(os.scandir(MEM), key=lambda x: x.name):
        if e.is_file() and re.search(r'config|attractor|possible|reachable|field', e.name, re.I):
            print("  %s (%d bytes)" % (e.name, e.stat().st_size))

print("\n(READ-ONLY. Fast + bounded. Grounds the Configuration-Space + attractor-discovery build.)")
