#!/usr/bin/env python3
"""sync_targeted_patch.py — make [DO: both ...] fire per-toy TARGETED patterns, not a broadcast.

The probe showed a toy-targeted Pattern makes Tenera's suction oscillate dramatically, while a
broadcast (no `toy`) leaves it steady even at 600ms. So sync sends each toy its own targeted
Pattern (still floored to 600 for both = lock-step). Idempotent; backs up device_patterns.py.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/device_patterns.py")
s = io.open(F, encoding="utf-8").read()

anchor = "                toy_link.send_pattern(None, _lv, _iv, _secs)   # broadcast = synced"
if anchor not in s:
    if "for _t in toy_link.TOYS:\n                    toy_link.send_pattern(_t, _lv, _iv, _secs)" in s:
        print("already patched — skipping"); raise SystemExit(0)
    print("MISS: broadcast sync line not found (run device_patterns_presets_patch first)")
    raise SystemExit(1)

repl = ("                for _t in toy_link.TOYS:\n"
        "                    toy_link.send_pattern(_t, _lv, _iv, _secs)   # per-toy targeted; broadcast didn't drive Tenera dramatically")
s = s.replace(anchor, repl, 1)

shutil.copy(F, F + ".bak-synctgt-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — sync now fires targeted patterns per toy (Tenera driven directly = dramatic)")
