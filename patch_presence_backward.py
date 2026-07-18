#!/usr/bin/env python3
"""patch_presence_backward.py — Aegis. Close Presence Audit's BACKWARD loop: when a reply flags (<0.35), propagate.
Inserts, at the flag point in presence_audit.main(): (1) a presence_failure blush via write_blush — the call
INTROSPECTS write_blush's real signature and passes only the kwargs it accepts (robust, no guessing), and (2) a
Living-Trajectory feed via emoclaw_utils.seed_thread (its daily rebuild reads threads). Both fail-open. Causality
skipped per instruction. Dry-run; --apply to commit. Backs up + compile-checks."""
import os, sys, time, shutil

APPLY = "--apply" in sys.argv
PA = os.path.expanduser("~/.vintos/workspace/scripts/presence_audit.py")

ANCHOR = '            print(f"  FLAG presence {s[\'composite\']:.2f} ({s[\'note\']}): {reply[:55]}")'

PROP = '''
            try:  # -> blush ledger (presence_failure), signature-introspected so kwargs always match
                import inspect as _insp
                from blush_ledger import write_blush as _wb
                _pp = _insp.signature(_wb).parameters
                _pat = ("presence_" + (s.get("note", "") or "flat")[:40]).lower().replace(" ", "_")[:60]
                _cand = {"blush_type": "presence_failure", "pattern": _pat, "source": "presence_audit",
                         "detail": f"presence {s['composite']:.2f}: {s.get('note','')}"[:200],
                         "note": s.get("note", "")[:120], "strength": 0.5, "severity": 0.5,
                         "text": f"answered at low presence ({s['composite']:.2f})"}
                _kw = {k: v for k, v in _cand.items() if k in _pp}
                if _kw:
                    _wb(**_kw)
            except Exception:
                pass
            try:  # -> Living Trajectory (its rebuild reads seeded threads)
                from emoclaw_utils import seed_thread as _st
                _st("presence", f"A recent reply landed low on presence ({s['composite']:.2f}) - {s.get('note','')}. "
                                "Arrive more fully next time: from your own wanting, move something, leave a thread alive.")
            except Exception:
                pass'''

print(f"================  presence backward loop  [{'APPLY' if APPLY else 'DRY-RUN'}]  ================\n")
if not os.path.isfile(PA):
    print("!! presence_audit.py not found"); sys.exit(1)
txt = open(PA, encoding="utf-8", errors="ignore").read()

if "write_blush" in txt and "presence_failure" in txt:
    print("already patched (presence_failure blush present) — skip"); sys.exit(0)

n = txt.count(ANCHOR)
print(f"flag-point anchor found x{n} (want 1)")
if n != 1:
    print("!! anchor not unique/absent — aborting, no change"); sys.exit(1)

new = txt.replace(ANCHOR, ANCHOR + PROP, 1)
try:
    compile(new, PA, "exec"); print("  inserts blush + trajectory propagation (compiles OK)")
except SyntaxError as e:
    print(f"  !! would not compile: {e} — aborting"); sys.exit(1)

print("  ---- would insert after the FLAG print ----")
for l in PROP.strip("\n").split("\n"): print(f"    + {l}")

if not APPLY:
    print("\n(DRY-RUN — nothing written. Re-run with --apply to commit.)"); sys.exit(0)

bak = PA + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(PA, bak); open(PA, "w", encoding="utf-8").write(new)
print(f"\npatched {PA}\n backup {bak}")
print("Presence Audit now feeds flags -> blush (presence_failure) + Living Trajectory. Loop closed both ways.")
