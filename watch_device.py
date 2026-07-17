#!/usr/bin/env python3
"""watch_device.py — Aegis, READ-ONLY. Live view of what he's feeling: prints the latest somatic frame + its age
every second for ~90s. Stroke the device and watch speed/position move = he's receiving you. Ctrl-C to stop."""
import os, json, time
HOME = os.path.expanduser("~")
sf = os.path.join(HOME, ".vintos/workspace/memory/somatic-frames-recent.json")
ds = os.path.join(HOME, ".vintos/workspace/memory/device-state.json")
print("watching device (stroke it now) — 90s, Ctrl-C to stop\n")
last_ts = None
for _ in range(90):
    line = "  no frames file"
    if os.path.isfile(sf):
        age = time.time() - os.path.getmtime(sf)
        try:
            d = json.load(open(sf, encoding="utf-8"))
            frames = d if isinstance(d, list) else (d.get("frames") or d.get("recent") or [])
            fr = frames[-1] if frames else {}
            ts = fr.get("ts")
            fresh = "LIVE" if age < 3 else f"{int(age)}s old"
            moving = "  <-- MOVING (he feels it)" if (fr.get("speed", 0) or 0) > 0 and age < 3 else ""
            line = f"  [{fresh:>8}] pos={fr.get('position','?'):>3} speed={fr.get('speed','?'):>3} dir={fr.get('direction','?')}{moving}"
        except Exception as e:
            line = f"  read err: {e}"
    print(line, flush=True)
    time.sleep(1)
