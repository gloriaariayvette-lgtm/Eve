#!/usr/bin/env python3
"""swap_grok_to_shim.py — Aegis. Point the grok chat scripts at the local Claude shim by swapping their base URL
https://api.x.ai/v1 -> http://127.0.0.1:8599/v1 (chat -> Claude+grok-fallback via the shim; image/video/other
paths pass through the shim to real grok). DRY-RUN by default; --apply backs up every file first.
EXCLUDED (stay pointing directly at x.ai): server.py (its grok calls are the model_router FALLBACK), model_router.py
(source of truth), briefing-audio.sh (voice), model_config.py (shared config server may use). Reversible."""
import os, glob, time, shutil, sys
HOME = os.path.expanduser("~")
APPLY = "--apply" in sys.argv
EXCLUDE = {"server.py", "model_router.py", "briefing-audio.sh", "model_config.py"}
DIRS = [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")]
BK = os.path.join(HOME, ".vintos", "grok-swap-backup-" + time.strftime("%Y%m%d-%H%M%S"))
print(("APPLY — writing (backup: " + BK.replace(HOME, "~") + ")") if APPLY else "DRY RUN — nothing written. Re-run with --apply to swap.")
print()

def swap_text(t):
    n = t.count("https://api.x.ai/v1"); t = t.replace("https://api.x.ai/v1", "http://127.0.0.1:8599/v1")
    m = t.count("https://api.x.ai");    t = t.replace("https://api.x.ai", "http://127.0.0.1:8599")
    return t, n + m

changed = excluded = 0
files = sorted(set(sum([glob.glob(os.path.join(d, "*.py")) + glob.glob(os.path.join(d, "*.sh")) for d in DIRS], [])))
print("== will swap ==")
for f in files:
    name = os.path.basename(f)
    try: txt = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if "api.x.ai" not in txt: continue
    if name in EXCLUDE:
        excluded += 1; continue
    new, cnt = swap_text(txt)
    if cnt == 0: continue
    residual = new.count("api.x.ai")
    print(f"  {f.replace(HOME,'~')}  ({cnt} URL{'s' if cnt!=1 else ''}" + (f", {residual} api.x.ai left!" if residual else "") + ")")
    changed += 1
    if APPLY:
        os.makedirs(BK, exist_ok=True)
        shutil.copy2(f, os.path.join(BK, name))
        open(f, "w", encoding="utf-8").write(new)

print(f"\n== left on x.ai (excluded / voice / fallback) ==")
for f in files:
    name = os.path.basename(f)
    try: txt = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if "api.x.ai" in txt and name in EXCLUDE:
        print(f"  {name}")

print(f"\n{'SWAPPED' if APPLY else 'would swap'} {changed} files; {excluded} excluded.")
if not APPLY: print("Review, then re-run with --apply.")
else: print(f"revert: cp {BK.replace(HOME,'~')}/* back, or restore per-file.")
