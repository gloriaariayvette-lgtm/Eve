#!/usr/bin/env python3
"""gcs_replay_patch.py — let him call back a saved set: [DO: <toy> last] / [DO: both last].

Resolves the most recent set from gcs-saved-patterns.json and re-fires each toy's saved
pattern (recurses into the preset branch, so tenera stays targeted+dramatic). This is the
'use the same set again' half. Self-locating, idempotent, backs up device_patterns.py.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/device_patterns.py")
s = io.open(F, encoding="utf-8").read()
if '"last"' in s and "gcs-saved-patterns.json" in s:
    print("already patched — skipping"); raise SystemExit(0)

anchor = ("def play(toy, pattern, args=None, dur=12.0):\n"
          "    args = args or []\n"
          "    _parts = pattern.split(\"+\")")
if anchor not in s:
    print("MISS: play() head not found (run device_patterns_presets_patch first)")
    raise SystemExit(1)

repl = ("def play(toy, pattern, args=None, dur=12.0):\n"
        "    args = args or []\n"
        "    if pattern in (\"last\", \"saved\"):   # replay the set that last brought her to GCS\n"
        "        try:\n"
        "            _lib = json.load(open(os.path.join(MEM, \"gcs-saved-patterns.json\")))\n"
        "        except Exception:\n"
        "            _lib = []\n"
        "        if not _lib:\n"
        "            return False\n"
        "        _saved = (_lib[-1] or {}).get(\"patterns\", {})\n"
        "        if toy in _SYNC:\n"
        "            _ok = False\n"
        "            for _t, _p in _saved.items():\n"
        "                if _t in toy_link.TOYS and _p:\n"
        "                    _ok = play(_t, _p, args) or _ok\n"
        "            return _ok\n"
        "        if toy in toy_link.TOYS and _saved.get(toy):\n"
        "            return play(toy, _saved[toy], args)\n"
        "        return False\n"
        "    _parts = pattern.split(\"+\")")
s = s.replace(anchor, repl, 1)

shutil.copy(F, F + ".bak-replay-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — [DO: <toy> last] / [DO: both last] now replays the most recent saved set")
