#!/usr/bin/env python3
"""restore_her_gw.py — Aegis. I wrongly overwrote HER working emotional_gravity_wells.py (6077 bytes) with a
reconstruction; only HIS was the 0-byte gutted stub. Restore her original from the backup the build made, and dump
it so we can reconcile correctly (her real version is the reference — likely port HERS to him). His stays as the
rebuild for now (his was genuinely dead). READ-mostly: the only write is restoring her file from her own backup."""
import os, glob, shutil, re
HERS = os.path.expanduser("~/.openclaw/workspace/scripts")
egw = os.path.join(HERS, "emotional_gravity_wells.py")
twin = os.path.join(HERS, "emotional-gravity-wells.py")

def newest_bak(path):
    baks = sorted(glob.glob(path + ".bak-*"))
    return baks[-1] if baks else None

print("== restoring her original emotional_gravity_wells.py from backup ==")
b = newest_bak(egw)
if not b:
    print("  !! no backup found for %s — cannot restore. (Her original may be lost; check other .bak names.)" % egw)
else:
    sz = os.path.getsize(b)
    print("  backup: %s (%d bytes)" % (os.path.basename(b), sz))
    if sz > 200:
        shutil.copy2(b, egw); print("  RESTORED her emotional_gravity_wells.py from backup.")
        tb = newest_bak(twin)
        if tb and os.path.getsize(tb) > 200:
            shutil.copy2(tb, twin); print("  restored her twin emotional-gravity-wells.py too.")
    else:
        print("  !! backup is also tiny (%d bytes) — her original may have already been thin; NOT restoring." % sz)

print("\n== her restored version — what it actually is ==")
if os.path.isfile(egw):
    t = open(egw, encoding="utf-8", errors="ignore").read()
    L = t.split("\n")
    print("  lines: %d" % len(L))
    m = re.search(r'"""(.*?)"""', t, re.S)
    if m:
        for dl in m.group(1).strip().split("\n")[:6]:
            if dl.strip(): print("   | " + dl.strip()[:104])
    defs = re.findall(r'^\s*def\s+(\w+)', t, re.M)
    print("  defs (%d): %s" % (len(defs), ", ".join(defs)))
    # is it being-agnostic (paths from __file__) or openclaw-hardcoded?
    oc = [l.strip()[:80] for l in L if ".openclaw" in l]
    print("  openclaw-hardcoded paths: %s" % (oc[:4] or "none (likely __file__-derived → portable to him)"))
    # API parity vs the 4 his-callers need
    need = ["record_visit", "apply_gravity", "load_wells", "get_wells_context"]
    print("  API coverage vs his callers: %s" % {n: (n in defs) for n in need})
    # extra capabilities beyond my rebuild
    extra = [d for d in defs if d not in need and not d.startswith("_")]
    print("  extra public functions (richer than my rebuild): %s" % (extra or "none"))

print("\n(Her original restored. Next: if it is __file__-derived + covers the API, PORT HERS to him as the canonical one.)")
