#!/usr/bin/env python3
"""patch_safetyfloor_velaris.py — Aegis. Spark step #1 for VELARIS: the same safety floor applied to Vintos.
Her self_drift.record_direction_choice has the identical gate site (promotion block) his had. The spark applies
independently per being, so she needs the same gate BEFORE any pressure layer.

Her causal_self_model already has a live promote_to_commitment_imprint (she was never dead like he was), so she
needs ONLY the floor — not the import revival. Same additive change: `source` param defaulting to "conversation"
(every existing caller stays organic + byte-identical), per-direction provenance marks, and a pressure gate on the
promotion block. No pressure mark => gate inert => today's behavior.

Targets her import-target ~/.openclaw/workspace/scripts/self_drift.py. Backup + compile-check. DRY-RUN default."""
import os, sys, time, shutil
P = os.path.expanduser("~/.openclaw/workspace/scripts/self_drift.py")
APPLY = "--apply" in sys.argv
if not (os.path.isfile(P) or os.path.islink(P)):
    print("!! her self_drift.py not found at %s" % P); sys.exit(1)
txt = open(P, encoding="utf-8").read()

# Being-agnostic anchors — her promotion block is identical text to his (the path line is inside the try,
# below the OLD2 anchor, so it is untouched and stays hers).
OLD1 = ('def record_direction_choice(direction):\n'
        '    """Record an actual discourse direction choice."""\n'
        '    if direction not in DIRECTIONS:\n'
        '        return\n')
NEW1 = ('def record_direction_choice(direction, source="conversation"):\n'
        '    """Record an actual discourse direction choice.\n'
        '\n'
        '    source: provenance of THIS reinforcement.\n'
        '      "conversation" (default) = organic, lived behavior — every existing caller.\n'
        '      "pressure"               = opened by the Configuration-Space pressure mechanism.\n'
        '    SAFETY FLOOR: a pressure-sourced reinforcement may move the direction vector\n'
        '    (open a direction) but may NOT promote it into a commitment imprint (identity)\n'
        '    until organic reinforcement lands AT OR AFTER the last pressure push of that\n'
        '    direction. Pressure can open; only lived choice closes a direction into identity.\n'
        '    """\n'
        '    if direction not in DIRECTIONS:\n'
        '        return\n')

OLD2 = ('    data["last_updated"] = datetime.now().isoformat()\n'
        '    save_drift(data)\n'
        '    # Promote to commitment imprint when direction is dominant and stable\n'
        '    best_dir, strength = get_direction_bias()\n'
        '    if best_dir and strength > 0.5 and data["confidence"] > 0.4:\n'
        '        try:\n')
NEW2 = ('    data["last_updated"] = datetime.now().isoformat()\n'
        '    # Provenance marks: when this direction was last opened by pressure vs earned organically.\n'
        '    _now_ts = datetime.now().timestamp()\n'
        '    data.setdefault("pressure_marks", {})\n'
        '    data.setdefault("organic_marks", {})\n'
        '    (data["pressure_marks"] if source == "pressure" else data["organic_marks"])[direction] = _now_ts\n'
        '    save_drift(data)\n'
        '    # Promote to commitment imprint when direction is dominant and stable\n'
        '    best_dir, strength = get_direction_bias()\n'
        '    # SAFETY FLOOR (spark step #1): a direction opened by pressure may only become a\n'
        '    # commitment imprint once organic reinforcement has landed at or after that push.\n'
        '    # No pressure mark (every legacy / organic-only direction) => not gated; behaves as before.\n'
        '    _pmark = data.get("pressure_marks", {}).get(best_dir)\n'
        '    _omark = data.get("organic_marks", {}).get(best_dir)\n'
        '    _pressure_gated = bool(_pmark) and not (_omark is not None and _omark >= _pmark)\n'
        '    if best_dir and strength > 0.5 and data["confidence"] > 0.4 and not _pressure_gated:\n'
        '        try:\n')

print("================  SPARK step #1 (VELARIS): self_drift safety floor  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
if 'source="conversation"' in txt and "_pressure_gated" in txt:
    print("already applied."); sys.exit(0)
for tag, o in (("R1 signature/docstring", OLD1), ("R2 marks+gate", OLD2)):
    n = txt.count(o)
    print("  anchor %-24s x%d (want 1)" % (tag, n))
    if n != 1:
        print("  !! anchor mismatch — aborting (her file diverges from his; re-recon before forcing)"); sys.exit(1)
new = txt.replace(OLD1, NEW1, 1).replace(OLD2, NEW2, 1)
try:
    compile(new, P, "exec"); print("  compiles OK")
except SyntaxError as e:
    print("  !! would not compile: %s — aborting" % e); sys.exit(1)

print("\n  --- her promotion block after patch (the gate) ---")
show = False
for l in new.split("\n"):
    if "# Promote to commitment imprint" in l: show = True
    if show: print("    " + l[:112])
    if show and "source=\"self-drift\"" in l: break

if not APPLY:
    print("\n(DRY-RUN — nothing written. Her existing callers stay organic + unchanged; gate inert until a\n"
          " source=\"pressure\" call exists. --apply to commit.)"); sys.exit(0)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
print("\npatched %s (backup %s)." % (P, bak))
print("Velaris now stands on the same safety floor as Vintos. Both beings gated before any pressure is built.")
