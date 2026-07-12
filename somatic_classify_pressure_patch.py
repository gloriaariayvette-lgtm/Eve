#!/usr/bin/env python3
"""somatic_classify_pressure_patch.py — infer graded pressure in classify().

No force sensor exists; pressure is INFERRED from motion: a squeeze reads as slow + pinned
toward an end + jitter (from the captured data). A fast stroke -> ~0 pressure. Adds
pressure(0-1), pressure_dir(building/easing/steady from speed trend), and zone(base/middle/tip)
to the classifier dict; existing keys untouched. Idempotent; backs up somatic_bridge.py.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/somatic_bridge.py")
s = io.open(F, encoding="utf-8").read()
if '"pressure"' in s:
    print("already patched — skipping"); raise SystemExit(0)

anchor = ('    return {"state": state, "center": sum(pos)/len(pos), "sweep": sweep,\n'
          '            "speed": mean_speed, "flips": flips}')
if anchor not in s:
    print("MISS: classify() return block not found"); raise SystemExit(1)

repl = ('    _ctr = sum(pos) / len(pos)\n'
        '    _slow = max(0.0, 1 - mean_speed / 30.0)                 # 1 when still, 0 when stroking fast\n'
        '    _pin = max(0.0, 1 - min(_ctr, 100 - _ctr) / 35.0)       # 1 pinned to an end, 0 at mid\n'
        '    _jit = min(1.0, flips / 6.0)                            # working/gripping a spot\n'
        '    _pressure = round(_slow * (0.6 * _pin + 0.4 * _jit), 2) # inferred: only when slow, shaped by pin+jitter\n'
        '    _h = len(spd) // 2 or 1\n'
        '    _trend = (sum(spd[_h:]) / max(1, len(spd) - _h)) - (sum(spd[:_h]) / _h)\n'
        '    _pdir = "building" if _trend < -6 else "easing" if _trend > 6 else "steady"\n'
        '    _zone = "base" if _ctr < 30 else "tip" if _ctr > 70 else "middle"\n'
        '    return {"state": state, "center": _ctr, "sweep": sweep,\n'
        '            "speed": mean_speed, "flips": flips,\n'
        '            "pressure": _pressure, "pressure_dir": _pdir, "zone": _zone}')
s = s.replace(anchor, repl, 1)

shutil.copy(F, F + ".bak-pressure-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — classify() now emits graded pressure + pressure_dir + zone")
