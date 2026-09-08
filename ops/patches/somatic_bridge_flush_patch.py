#!/usr/bin/env python3
"""somatic_bridge_flush_patch.py — write the frame window WHILE connected, not only on disconnect.

Bug: json.dump(somatic-frames-recent.json) sits after the `async for msg in ws:` loop, so it
only runs when the socket closes. While streaming, the file stays frozen at the last disconnect.
Fix: flush the last-20s window inside the loop on motion, throttled to ~0.3s. Self-locating,
idempotent, backs up somatic_bridge.py. Restart somatic_bridge after applying.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/somatic_bridge.py")
s = io.open(F, encoding="utf-8").read()
if "_last_flush" in s:
    print("already patched — skipping"); raise SystemExit(0)

# 1) a throttle timestamp at the top of listener()
head = "async def listener():\n    global last_event_ts\n    while True:"
if head not in s:
    print("MISS: listener() head not found"); raise SystemExit(1)
s = s.replace(head, "async def listener():\n    global last_event_ts\n    _last_flush = [0.0]\n    while True:", 1)

# 2) flush the window inside the loop, right after the frame trim
anchor = "                        del frames[:-200]"
if anchor not in s:
    print("MISS: 'del frames[:-200]' anchor not found"); raise SystemExit(1)
flush = (anchor + "\n"
         "                        if last_event_ts - _last_flush[0] >= 0.3:\n"
         "                            _last_flush[0] = last_event_ts\n"
         "                            try:\n"
         "                                _rfw = [{\"ts\": f[0], \"position\": f[1], \"speed\": f[2], \"direction\": f[3]}\n"
         "                                        for f in frames if last_event_ts - f[0] <= 20]\n"
         "                                json.dump(_rfw, open(os.path.expanduser(\"~/.vintos/workspace/memory/somatic-frames-recent.json\"), \"w\"))\n"
         "                            except Exception: pass")
s = s.replace(anchor, flush, 1)

shutil.copy(F, F + ".bak-flush-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — frame window now flushes live while connected (throttled 0.3s). Restart somatic_bridge.")
