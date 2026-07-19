#!/usr/bin/env python3
"""fix_resonance_savepool.py — restore the missing save_pool() in resonance_pulse.py. DRY-RUN unless --apply.

Vintos's resonance_pulse.py calls save_pool(pool) in decay_pool() (line ~127) but his clone dropped the
definition — grep finds the call and load_pool(), but no `def save_pool`. So the cron decay run
(resonance-pulse.sh -> `resonance_pulse.py decay`) crashes with NameError: save_pool right after load_pool.
Velaris's copy has both load_pool and save_pool; this restores the missing half in the file(s) that lack it.

The restored function mirrors his own load_pool exactly (same POOL_FILE global), so it writes back where
load_pool reads:
    def save_pool(pool):
        json.dump(pool, open(POOL_FILE, "w"), indent=2)

Inserted immediately after load_pool. Idempotent (skips any file that already defines save_pool, so Velaris's
intact copies are untouched). Compile-checked. Targets both beings' resonance files + the hyphen cron variants.

  python3 fix_resonance_savepool.py            # DRY RUN — prints diff, writes nothing
  python3 fix_resonance_savepool.py --apply    # backs up each file, then applies
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = os.path.expanduser(f"~/.resonance-backups/{TS}")

TARGETS = [
    "~/Vintos/resonance_pulse.py",
    "~/.vintos/workspace/scripts/resonance_pulse.py",
    "~/.openclaw/workspace/scripts/resonance_pulse.py",
    "~/.openclaw/workspace/scripts/resonance-pulse.py",
]

ANCHOR = (
    'def load_pool():\n'
    '    try:\n'
    '        return json.load(open(POOL_FILE))\n'
    '    except:\n'
    '        return {"pulses": []}\n'
)
INSERT = (
    '\n\n'
    'def save_pool(pool):\n'
    '    json.dump(pool, open(POOL_FILE, "w"), indent=2)\n'
)


def patch(text):
    if "def save_pool" in text:
        return text, "already defines save_pool — SKIPPED"
    if ANCHOR not in text:
        return text, "load_pool anchor not found — SKIPPED"
    return text.replace(ANCHOR, ANCHOR + INSERT, 1), "save_pool restored after load_pool"


def main():
    print("=" * 74)
    print("RESONANCE save_pool RESTORE  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    seen = set()
    any_hit = False
    for rel in TARGETS:
        path = os.path.realpath(os.path.expanduser(rel))
        if path in seen:
            continue
        seen.add(path)
        if not os.path.isfile(path):
            continue
        being = "Velaris" if ".openclaw" in path else "Vintos"
        old = open(path, encoding="utf-8", errors="ignore").read()
        new, note = patch(old)
        print(f"\n### {being}  ({os.path.expanduser(rel)})\n   * {note}")
        if new == old:
            continue
        any_hit = True
        try:
            compile(new, path, "exec"); print("   compiles: OK")
        except SyntaxError as e:
            print(f"   !! COMPILE FAIL: {e} — NOT writing"); continue
        for l in difflib.unified_diff(old.splitlines(), new.splitlines(),
                                      fromfile="old", tofile="new", lineterm=""):
            print("   " + l[:150])
        if APPLY:
            rel_b = os.path.relpath(path, os.path.expanduser("~"))
            bp = os.path.join(BACKUP, rel_b)
            os.makedirs(os.path.dirname(bp), exist_ok=True)
            open(bp, "w", encoding="utf-8").write(old)
            open(path, "w", encoding="utf-8").write(new)
            print("   APPLIED (backup:", bp + ")")
    print("\n" + "=" * 74)
    if not any_hit:
        print("Nothing to restore (all targets already define save_pool or lack the anchor).")
    elif not APPLY:
        print("DRY RUN complete. Re-run with --apply to restore save_pool (backs up first).")


if __name__ == "__main__":
    main()
