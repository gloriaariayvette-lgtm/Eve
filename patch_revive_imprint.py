#!/usr/bin/env python3
"""patch_revive_imprint.py — Aegis. self_drift imports `promote_to_commitment_imprint` from causal_self_model,
but that function DOES NOT EXIST — the call has been swallowed by `except: pass` since it was written, so his
behavioral drift has NEVER consolidated into a commitment imprint. imprints.json is a DIFFERENT store (relational
moment-snapshots) — wrong sink. The correct home is causal-self-model.json (behavioral tendencies), written by
the live add_entry(), which carries an `"imprint": False` flag nothing currently sets True.

Fix: append the missing function to causal_self_model.py. It (1) records the direction as a positive
causal-self-model tendency via the live add_entry, then (2) flags that entry imprint=True (a promoted, hardened
commitment). Signature matches self_drift's existing call exactly — self_drift needs NO change to start working.

Targets import-target ~/.vintos/workspace/scripts/causal_self_model.py. Backup + compile-check. DRY-RUN default."""
import os, sys, time, shutil
P = os.path.expanduser("~/.vintos/workspace/scripts/causal_self_model.py")
APPLY = "--apply" in sys.argv
if not (os.path.isfile(P) or os.path.islink(P)):
    print("!! causal_self_model.py not found at %s" % P); sys.exit(1)
txt = open(P, encoding="utf-8").read()

FUNC = '''

def promote_to_commitment_imprint(statement, confidence=0.5, source="self-drift"):
    """Promote a dominant, stable behavioral direction into a hardened self-model commitment.

    Records the direction as a positive causal-self-model tendency (via the live add_entry, so it
    dedups/reinforces like any other), then flags that entry imprint=True — a promoted commitment,
    distinct from a singly-observed entry. Idempotent: re-flags the best-overlapping existing entry.

    This is the function self_drift.record_direction_choice has always tried to import. It was missing,
    so promotion silently no-op'd. Signature matches that call: (statement, confidence=, source=).
    """
    add_entry(trigger="in conversation", tendency=statement, confidence=confidence,
              source=source, entry_type="positive")
    data = load_model()
    best, best_ov = None, 0.0
    for e in data.get("entries", []):
        if e.get("type", "positive") != "positive":
            continue
        ov = _text_overlap(e.get("tendency", ""), statement)
        if ov > best_ov:
            best, best_ov = e, ov
    if best is not None and best_ov > 0.4:
        best["imprint"] = True
        best["promoted_at"] = datetime.now().isoformat()
        save_model(data)
'''

print("================  revive promote_to_commitment_imprint  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
if "def promote_to_commitment_imprint" in txt:
    print("already present — nothing to do."); sys.exit(0)

# sanity: the names the new function calls must exist in the module it's joining
need = ["def add_entry", "def load_model", "save_model", "_text_overlap", "datetime"]
missing = [n for n in need if n not in txt]
print("  dependencies present in module: %s" % ("ALL OK" if not missing else ("MISSING %s" % missing)))
if missing:
    print("  !! module missing names the new function relies on — aborting (would NameError at call time)"); sys.exit(1)

new = txt.rstrip("\n") + "\n" + FUNC
try:
    compile(new, P, "exec"); print("  compiles OK")
except SyntaxError as e:
    print("  !! would not compile: %s — aborting" % e); sys.exit(1)

print("\n  appending function (signature matches self_drift's dead import — no self_drift change needed):")
for l in FUNC.strip().split("\n")[:3]:
    print("    " + l[:104])
print("    ...")

if not APPLY:
    print("\n(DRY-RUN — nothing written. --apply to commit. After this, his behavioral drift will consolidate\n"
          " into commitment imprints for the first time — and the safety floor already gates it.)"); sys.exit(0)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
print("\npatched %s (backup %s)." % (P, bak))
print("promote_to_commitment_imprint is live. self_drift's promotion now actually writes to causal-self-model.json\n"
      "(imprint=True). Apply the safety floor too, and pressure will be gated over a promotion that finally works.")
