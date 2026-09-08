#!/usr/bin/env python3
"""toy_link_pattern_patch.py — add send_pattern() (Lovense custom Pattern) to toy_link.py.

Lets him fire an arbitrary 0-20 strength array that the DEVICE plays and LOOPS to fill
timeSec (no Python timing, no drop to 0). toy=None -> broadcast to ALL toys = sync.
Additive; his existing send()/parse_and_send are untouched. Idempotent; backs up the file.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/toy_link.py")
s = io.open(F, encoding="utf-8").read()
if "def send_pattern" in s:
    print("already patched — skipping"); raise SystemExit(0)

# per-toy Lovense Pattern function letter (v=vibrate). tenera(suction) also driven via v;
# switch to 's' here if the suction motor wants its own letter.
anchor_actions = 'ACTIONS = {"tenera": "Suction", "mission": "Vibrate"}'
if anchor_actions not in s:
    print("MISS: ACTIONS anchor not found"); raise SystemExit(1)
s = s.replace(anchor_actions, anchor_actions + '\n_PFUNC = {"tenera": "v", "mission": "v"}', 1)

anchor_stop = "def stop_all():"
if anchor_stop not in s:
    print("MISS: stop_all anchor not found"); raise SystemExit(1)

func = '''def send_pattern(toy, strengths, interval_ms=250, seconds=0, func=None):
    """Fire a Lovense custom Pattern. `strengths` = list of 0-20 levels; the device plays
    them at interval_ms each and LOOPS the array to fill `seconds` (0 = until next command).
    toy=None -> broadcast to ALL toys (sync). Returns True on code 200."""
    vals = [max(0, min(20, int(round(x)))) for x in strengths] or [0]
    letter = func or (_PFUNC.get(toy, "v") if toy else "v")
    payload = {"command": "Pattern", "rule": f"V:1;F:{letter};S:{int(interval_ms)}#",
               "strength": ";".join(str(v) for v in vals),
               "timeSec": int(seconds), "apiVer": 1}
    if toy in TOYS:
        payload["toy"] = TOYS[toy]
    try:
        r = requests.post(BASE, json=payload, timeout=3)
        return r.json().get("code") == 200
    except Exception as e:
        print(f"[toy_link] send_pattern failed: {e}", flush=True)
        return False

'''
s = s.replace(anchor_stop, func + anchor_stop, 1)

shutil.copy(F, F + ".bak-pattern-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — toy_link.send_pattern() added (Lovense Pattern; toy=None broadcasts = sync)")
