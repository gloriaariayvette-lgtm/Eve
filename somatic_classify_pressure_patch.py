#!/usr/bin/env python3
"""somatic_classify_pressure_patch.py — infer press/grip in classify() (the last Claude's technique).

Validated on clean live data: a press/grip = a large position JUMP that happens while speed is
low (<=10) — displacement the stroking speed can't explain. A stroke's jumps happen at HIGH speed
(explained), so they read ~0. A perfectly-still held squeeze leaves no jump (blurs into hold) —
the honest hardware floor. Adds pressure(0-1 from the low-speed jump), pressure_dir (building/
easing from speed trend), and zone(base/middle/tip, descriptor only). Existing keys untouched.
Runs on the bridge's full in-memory stream. Idempotent; backs up somatic_bridge.py.
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
        '    _press = 0                                              # displacement the speed cannot explain = force\n'
        '    for _i in range(1, len(pos)):\n'
        '        if spd[_i] <= 10 and pos[_i - 1] > 0:               # a jump while barely stroking (skip 0-placement)\n'
        '            _press = max(_press, abs(pos[_i] - pos[_i - 1]))\n'
        '    _pressure = round(min(1.0, _press / 70.0), 2)           # inferred grip/press, graded by the low-speed jump\n'
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
print("PATCHED — classify() infers press/grip from the low-speed position jump (graded) + dir + zone")
