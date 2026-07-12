#!/usr/bin/env python3
"""somatic_felt_rewrite_patch.py — replace canned felt sentences with non-parrotable cues.

The old translate() returned finished, vivid sentences he echoed verbatim. This returns terse
multi-axis CUES he must render himself — where (zone) / motion (speed regime + sweep) / rhythm
(flips) / inferred pressure (+building/easing) — plus a shift:<prev>-><now> line (the turn-to-turn
transition, and the ledger bridge). Backward compatible: reads the new classify keys with
defaults, keeps the translate(c, prev_state=None) signature. Idempotent; backs up somatic_felt.py.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/somatic_felt.py")
s = io.open(F, encoding="utf-8").read()
if "read it, don't recite" in s or "feel it, do not recite" in s:
    print("already patched — skipping"); raise SystemExit(0)

start = s.find("def translate(c, prev_state=None):")
if start == -1:
    print("MISS: translate() not found"); raise SystemExit(1)
end = s.find("\ndef on_release", start)
if end == -1:
    print("MISS: end-of-translate anchor (on_release) not found"); raise SystemExit(1)

NEW = '''def translate(c, prev_state=None):
    """c = classifier dict. Returns terse felt CUES he renders himself, not a canned line."""
    state = c.get("state")
    if state == "absent":
        return None
    zone = c.get("zone", "middle"); speed = c.get("speed", 0); sweep = c.get("sweep", 0)
    flips = c.get("flips", 0); pressure = c.get("pressure", 0.0); pdir = c.get("pressure_dir", "steady")
    cues = []
    cues.append({"base": "low, at the base", "middle": "along the middle of you", "tip": "up near the tip"}.get(zone, "along you"))
    if speed >= 40:
        cues.append("fast, full-length" if sweep >= 50 else "fast, in short strokes")
    elif speed >= 12:
        cues.append("a steady, unhurried rhythm")
    elif speed > 0:
        cues.append("barely traveling, slow")
    else:
        cues.append("no travel — held")
    if flips >= 3:
        cues.append("changing direction over and over")
    elif flips == 2:
        cues.append("reversing on you")
    if pressure >= 0.55:
        cues.append("a squeezing grip" + ("" if pdir == "steady" else ", " + pdir))
    elif pressure >= 0.3:
        cues.append(("pressure gathering, " + pdir) if pdir != "steady" else "a firm, closing hold")
    line = "; ".join(cues)
    shift = ("  (shift: %s -> %s)" % (prev_state, state)) if (prev_state and prev_state != state) else ""
    return "[YOUR BODY, RIGHT NOW — feel it, do not recite it] " + line + "." + shift

'''

s = s[:start] + NEW + s[end + 1:]   # +1 drops the leading newline before \ndef on_release
shutil.copy(F, F + ".bak-feltrw-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — translate() now emits non-parrotable multi-axis cues + shift line")
