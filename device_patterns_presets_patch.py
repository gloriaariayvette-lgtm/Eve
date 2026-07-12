#!/usr/bin/env python3
"""device_patterns_presets_patch.py — named presets + compose + sync + loop for his body.

Adds a PRESETS table (the Pattern Mixer shapes as 0-20 strength arrays), and extends play()
so he can fire them by name via the Lovense Pattern command (device loops them natively —
no drop to 0). Grammar, all through his existing [DO:] tags:
  [DO: mission cake]            -> play the 'cake' curve, looping
  [DO: mission cake+zigzag+soft]-> compose (arrays concatenated) into one extended pattern
  [DO: both cake]               -> broadcast to all toys, synced
  [DO: mission cake 60]         -> loop for 60s (0/omitted = until his next directive)
His throb/pulse/build/wave/steady/still are untouched. Idempotent; backs up the file.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/device_patterns.py")
s = io.open(F, encoding="utf-8").read()
if "PRESETS" in s:
    print("already patched — skipping"); raise SystemExit(0)

# 1) widen the [DO:] pattern group so 'cake+zigzag' is captured (was (\w+))
old_dir = r'_DIR = re.compile(r"\[DO:\s*(\w+)\s+(\w+)((?:\s+\d+)*)\s*\]", re.I)'
new_dir = r'_DIR = re.compile(r"\[DO:\s*(\w+)\s+([\w+]+)((?:\s+\d+)*)\s*\]", re.I)'
if old_dir not in s:
    print("MISS: _DIR regex not found"); raise SystemExit(1)
s = s.replace(old_dir, new_dir, 1)

# 2) preset table + compose helper, inserted before play()
TABLE = '''# --- Pattern Mixer presets as 0-20 strength arrays: (levels, interval_ms). Tune by feel. ---
PRESETS = {
    "low": ([4], 400), "mid": ([10], 400), "high": ([16], 400),
    "wave1": ([2, 5, 9, 13, 17, 20, 17, 13, 9, 5, 2, 0], 300),          # long dramatic swells
    "wave2": ([4, 7, 10, 12, 13, 12, 10, 7, 4, 3], 300),                # like wave3 but smoother
    "wave3": ([3, 6, 9, 10, 9, 6, 3, 2, 3, 6, 9, 10, 9, 6, 3], 250),    # gentle rounded rolls
    "wave4": ([2, 20, 2, 20, 2, 20, 2, 20], 150),                       # brisk sharp sawtooth
    "square": ([20, 20, 20, 2, 2, 2, 20, 20, 20, 2, 2, 2], 250),        # abrupt on/off
    "step": ([3, 3, 7, 7, 11, 11, 15, 15, 20, 20, 20, 20], 300),        # staircase up + hold
    "climb": ([2, 4, 6, 9, 12, 15, 18, 20, 20, 20, 20, 20], 300),       # rise to sustained high
    "downhill": ([20, 20, 17, 14, 11, 8, 6, 4, 3, 2, 2], 300),          # wind-down
    "zigzag": ([2, 8, 14, 20, 14, 8, 2, 8, 14, 20, 14, 8, 2], 150),     # tall rapid triangle
    "spike": ([3, 3, 3, 20, 3, 3, 3, 3, 20, 3, 3], 200),                # calm broken by a jab
    "trapezold": ([2, 6, 10, 14, 18, 20, 20, 20, 20, 18, 14, 10, 6, 2], 250),  # ramp/hold/ramp
    "valley": ([14, 11, 8, 5, 3, 2, 3, 5, 8, 11, 14], 300),             # dip to a low lull
    "cake": ([3, 3, 8, 8, 14, 14, 20, 20, 20, 20, 20, 14, 8, 3], 250),  # layered rise to a swell
    "fireworks": ([4, 8, 20, 6, 3, 14, 20, 10, 3, 18, 20, 5], 200),     # irregular bursts
    "random": ([12, 3, 18, 7, 20, 2, 15, 9, 20, 5, 11, 17], 180),       # chaotic jitter
    "spark": ([2, 2, 2, 18, 20, 16, 20, 14, 2, 2, 2], 150),             # calm, flare, calm
    "soft": ([2, 3, 4, 5, 6, 5, 4, 3, 2, 3, 4, 5, 6, 5, 4, 3, 2], 350), # faint tender rise/fall
}
PRESETS["trapezoid"] = PRESETS["trapezold"]   # accept the correct spelling too
_SYNC = ("both", "all", "sync")

def _compose(names):
    """Concatenate the arrays of one or more preset names into one extended pattern.
    Returns (strengths, interval_ms) or ([], 0) if none are presets."""
    levels, interval = [], None
    for n in names:
        p = PRESETS.get(n)
        if not p:
            continue
        levels += list(p[0])
        if interval is None:
            interval = p[1]
    return levels, (interval or 250)


'''
anchor_play = "def play(toy, pattern, args=None, dur=12.0):"
if anchor_play not in s:
    print("MISS: play() def not found"); raise SystemExit(1)
s = s.replace(anchor_play, TABLE + anchor_play, 1)

# 3) preset/compose/sync branch at the very top of play(), before the TOYS guard
play_head = ('def play(toy, pattern, args=None, dur=12.0):\n'
             '    args = args or []\n'
             '    if toy not in toy_link.TOYS: return False')
if play_head not in s:
    print("MISS: play() head not found"); raise SystemExit(1)
new_head = ('def play(toy, pattern, args=None, dur=12.0):\n'
            '    args = args or []\n'
            '    _parts = pattern.split("+")\n'
            '    if any(p in PRESETS for p in _parts):\n'
            '        _lv, _iv = _compose(_parts)\n'
            '        if _lv:\n'
            '            _secs = int(args[0]) if args else 0            # 0 = loop until his next directive\n'
            '            _peak = max(_lv)\n'
            '            if toy in _SYNC:\n'
            '                for _t in toy_link.TOYS:\n'
            '                    _o = _threads.get(_t)\n'
            '                    if _o: _o.set()\n'
            '                toy_link.send_pattern(None, _lv, _iv, _secs)   # broadcast = synced\n'
            '                for _t in toy_link.TOYS:\n'
            '                    _mark(_t); _set_state(_t, intensity=_peak, pattern=pattern, set_by="him")\n'
            '                return True\n'
            '            if toy in toy_link.TOYS:\n'
            '                _o = _threads.get(toy)\n'
            '                if _o: _o.set()\n'
            '                toy_link.send_pattern(toy, _lv, _iv, _secs)\n'
            '                _mark(toy); _set_state(toy, intensity=_peak, pattern=pattern, set_by="him")\n'
            '                return True\n'
            '            return False\n'
            '    if toy not in toy_link.TOYS: return False')
s = s.replace(play_head, new_head, 1)

shutil.copy(F, F + ".bak-presets-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — PRESETS + compose + sync + device-loop added to play(); _DIR widened for '+'")
print("  try: [DO: mission cake]  ·  [DO: mission cake+zigzag+soft]  ·  [DO: both cake]")
