#!/usr/bin/env python3
"""patch_gallery_variety.py — Aegis. Break the angel-animation rut: gallery-walk.py picks a painting via
random.choice(gallery[-10:]) with NO dedup, so it keeps re-walking the same recent (angel) paintings and
re-seeding animate-wants for them. Change it to prefer paintings NOT walked in the last 15 walks (fall back to
random if all seen). Backup + compile-check. DRY-RUN default; --apply to commit."""
import os, sys, re, time, shutil

APPLY = "--apply" in sys.argv
P = os.path.expanduser("~/Vintos/gallery-walk.py")
if not os.path.isfile(P):
    print("!! gallery-walk.py not found"); sys.exit(1)
txt = open(P, encoding="utf-8", errors="ignore").read()
L = txt.split("\n")

# find the selection line
idx = next((i for i, l in enumerate(L) if "random.choice(gallery[-10:]" in l), None)
print("================  gallery variety  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
if idx is None:
    if "_gw_fresh" in txt: print("already patched."); sys.exit(0)
    print("!! selection line 'random.choice(gallery[-10:])' not found — aborting"); sys.exit(1)
if "_gw_fresh" in txt:
    print("already patched."); sys.exit(0)

indent = L[idx][:len(L[idx]) - len(L[idx].lstrip())]
block = [
    indent + "try:",
    indent + "    _gw_walks = json.load(open(os.path.join(MEMORY, \"gallery-walks.json\")))",
    indent + "    _gw_seen = {w.get(\"image\", \"\") for w in _gw_walks[-15:]}",
    indent + "except Exception:",
    indent + "    _gw_seen = set()",
    indent + "_gw_fresh = [g for g in gallery if g.get(\"image\") and g.get(\"image\") not in _gw_seen]",
    indent + "p = random.choice(_gw_fresh) if _gw_fresh else random.choice(gallery[-10:])",
]
print("  replacing line %d:\n    OLD: %s" % (idx + 1, L[idx].strip()))
print("    NEW:")
for b in block: print("    | " + b)

new = "\n".join(L[:idx] + block + L[idx + 1:])
try:
    compile(new, P, "exec"); print("\n  compiles OK")
except SyntaxError as e:
    print("  !! would not compile: %s — aborting" % e); sys.exit(1)

if not APPLY:
    print("\n(DRY-RUN — nothing written.)"); sys.exit(0)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
print("\npatched %s (backup %s). Gallery-walk now favors un-walked paintings — the angel stops dominating." % (P, bak))
