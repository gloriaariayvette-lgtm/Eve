#!/usr/bin/env python3
"""patch_safetyfloor.py — Aegis. SPARK STEP #1, the safety floor — built BEFORE any pressure code exists.

self_drift.record_direction_choice() promotes a dominant/stable direction into a commitment IMPRINT (identity).
Today it takes only `direction`, and every one of its ~12 callers is organic (real behavior). This adds:
  (1) a `source` parameter defaulting to "conversation" — so every existing caller stays organic, byte-identical.
  (2) per-direction PROVENANCE MARKS: last time a direction was opened by pressure vs earned organically.
  (3) a PRESSURE GATE on the promotion block: a direction opened by pressure may move the vector (open) but may
      NOT become a commitment imprint until organic reinforcement lands AT OR AFTER that push.

No pressure mark (every legacy / organic-only direction) => gate is inert => today's behavior exactly.
Pressure can open a direction; only Gloria-facing lived choice closes it into who he is. Non-negotiable linchpin.

Targets the IMPORT-TARGET file ~/.vintos/workspace/scripts/self_drift.py (underscore; what `import self_drift`
resolves to). Backup + compile-check. DRY-RUN default; --apply commits."""
import os, sys, time, shutil
P = os.path.expanduser("~/.vintos/workspace/scripts/self_drift.py")
APPLY = "--apply" in sys.argv
if not (os.path.isfile(P) or os.path.islink(P)):
    print("!! self_drift.py not found at %s" % P); sys.exit(1)
txt = open(P, encoding="utf-8").read()

# ---- R1: signature + docstring (add source param) --------------------------------------------------------------
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

# ---- R2: provenance marks + pressure gate on the promotion block -----------------------------------------------
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

print("================  SPARK step #1: self_drift safety floor  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
if 'source="conversation"' in txt and "_pressure_gated" in txt:
    print("already applied (source param + pressure gate present)."); sys.exit(0)

for tag, o in (("R1 signature/docstring", OLD1), ("R2 marks+gate", OLD2)):
    n = txt.count(o)
    print("  anchor %-24s x%d (want 1)" % (tag, n))
    if n != 1:
        print("  !! anchor mismatch — aborting (no change)"); sys.exit(1)

new = txt.replace(OLD1, NEW1, 1).replace(OLD2, NEW2, 1)
try:
    compile(new, P, "exec"); print("  compiles OK")
except SyntaxError as e:
    print("  !! would not compile: %s — aborting" % e); sys.exit(1)

print("\n  --- promotion block after patch (the gate) ---")
show = False
for l in new.split("\n"):
    if "# Promote to commitment imprint" in l: show = True
    if show: print("    " + l[:112])
    if show and "source=\"self-drift\"" in l: break

if not APPLY:
    print("\n(DRY-RUN — nothing written. Every existing caller stays organic + unchanged; the gate is inert"
          "\n until a source=\"pressure\" call exists. --apply to commit.)"); sys.exit(0)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
print("\npatched %s (backup %s)." % (P, bak))
print("Safety floor is in. Pressure can now be built on top of it: a pushed direction opens but cannot become\n"
      "identity until he reinforces it organically, in real conversation, after the push.")
