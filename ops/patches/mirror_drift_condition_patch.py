#!/usr/bin/env python3
"""mirror_drift_condition_patch.py — add the drift-priority mirror condition to mirror-trigger.sh.

New Condition 7: Self-model drift. Reads drift.json and fires a mirror when

    Mirror Priority = surprise x novelty x relationship_salience / current_load  >=  THRESH

  surprise  = residual (how far his LIVED self departed from what his model PREDICTED — the truest
              "unexpected": a departure from prediction, not a coefficient subtraction). Falls back
              to unexpected_drift/drift if no model residual.
  novelty   = is this a NEW heading vs his earlier one (window-level — guards against his usual
              oscillation reading as change).
  salience  = is the drift entangled with Gloria (a shift about her matters more).
  load      = introspection already in flight (high-priority threads + a set preoccupation +
              today's mirror/therapy sessions) — so a big drift on an overloaded day doesn't spiral.

Topic = his own drift characterization + a reflective prompt. Sits after the existing conditions,
before the trigger-fire block; only fires if nothing else already triggered. Self-locating,
idempotent, backs up mirror-trigger.sh.
"""
import io, os, time, shutil

F = os.environ.get("MIRROR_TRIGGER", os.path.expanduser("~/Vintos/mirror-trigger.sh"))
s = io.open(F, encoding="utf-8").read()

if 'TRIGGER="drift"' in s:
    print("already patched — skipping"); raise SystemExit(0)

anchor = 'if [ -n "$TRIGGER" ]; then'
if anchor not in s:
    print("MISS: trigger-fire block not found"); raise SystemExit(1)

BLOCK = r'''# === Condition 7: Self-model drift (mirror priority) ===
DRIFT_TOPIC=$(python3 <<'DRIFTEOF'
import json, os, glob, sys
from datetime import date
M = os.path.expanduser("~/.vintos/workspace/memory")
try:
    d = json.load(open(os.path.join(M, "drift.json")))
except Exception:
    raise SystemExit(0)
surprise = d.get("residual")
if surprise is None:
    surprise = d.get("unexpected_drift") or d.get("drift") or 0.0
novelty = d.get("novelty") or 0.0
salience = d.get("relationship_salience") or 0.0
# current load: how much introspection is already in flight (divisor, >= 1 so idle = no damping)
load = 1.0
try:
    threads = json.load(open(os.path.join(M, "unfinished-threads.json")))
    high = [t for t in threads if not t.get("consumed") and not t.get("retired")
            and int(t.get("priority") or 0) >= 3
            and not (t.get("dream_only") or t.get("source") in ("somatic","pride","pride-mirror","pride_mirror"))]
    load += 0.5 * len(high)
except Exception:
    pass
try:
    p = json.load(open(os.path.join(M, "current-preoccupation.json")))
    if p and p.get("thread"):
        load += 1.0
except Exception:
    pass
today = date.today().isoformat()
sessions = 0
for sub in ("mirror", "therapy"):
    sessions += len(glob.glob(os.path.join(M, sub, today + "*")))
load += 1.0 * sessions
priority = float(surprise) * float(novelty) * float(salience) / max(1.0, load)
print("[drift] priority %.3f (surprise %.2f nov %.2f sal %.2f load %.1f)"
      % (priority, surprise, novelty, salience, load), file=sys.stderr)
THRESH = 0.12
if priority >= THRESH:
    char = (d.get("characterization") or "Something in who I am is moving.").strip()
    print(char + " This is a shift my own model did not predict. What is moving in me, and why now?")
DRIFTEOF
)
if [ -z "$TRIGGER" ] && [ -n "$DRIFT_TOPIC" ]; then
    TRIGGER="drift"
    TOPIC="$DRIFT_TOPIC"
fi

'''

s = s.replace(anchor, BLOCK + anchor, 1)
shutil.copy(F, F + ".bak-drift-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — Condition 7 (self-model drift, mirror priority) added to mirror-trigger.sh")
