#!/usr/bin/env python3
"""tenera_interval_patch.py — give Tenera (suction) a slower step so its shifts land dramatically.

Testing: a suction motor can't actuate at 150-250ms (blurs to 'steady'); at ~600ms the same
array oscillates hard, and the function letter (s vs v) made no difference — the step size was
everything. The device Pattern engine keeps transitions smooth (unlike timed Function calls),
so we keep it and just FLOOR the interval whenever Tenera is involved (its own patterns and
broadcast/sync). Mission stays fast when solo. Idempotent; backs up device_patterns.py.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/device_patterns.py")
s = io.open(F, encoding="utf-8").read()
if "_TENERA_MIN_IV" in s:
    print("already patched — skipping"); raise SystemExit(0)

anchor = "            _peak = max(_lv)"
if anchor not in s:
    print("MISS: preset branch anchor not found (run device_patterns_presets_patch first)")
    raise SystemExit(1)

ins = (anchor + "\n"
       "            _TENERA_MIN_IV = 600   # suction needs a slower step to actuate dramatically\n"
       "            if toy in _SYNC or toy == \"tenera\":\n"
       "                _iv = max(_iv, _TENERA_MIN_IV)")
s = s.replace(anchor, ins, 1)

shutil.copy(F, F + ".bak-tenera-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — Tenera-involved patterns floor the step at 600ms (dramatic suction); mission solo unchanged")
