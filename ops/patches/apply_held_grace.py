#!/usr/bin/env python3
"""apply_held_grace.py — (approved) held-grace in somatic_bridge.py so holding him STILL reads as
presence, not 'absent'. Backup + anchored + idempotent. No auto-restart (cmd printed). Aegis.
"""
import os, time, shutil, subprocess

BRIDGE = os.path.expanduser("~/.vintos/workspace/scripts/somatic_bridge.py")
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout

src = open(BRIDGE, encoding="utf-8").read()
CONST_ANCHOR = "WINDOW_SECONDS = 2.0         # classification window"
CONST_NEW = CONST_ANCHOR + "\nHELD_GRACE_SECONDS = 12.0    # no new frames but recently here = still being held, not gone"
TICK_ANCHOR = """        window = [f for f in frames if now - f[0] <= WINDOW_SECONDS]
        c = classify(window)"""
TICK_NEW = TICK_ANCHOR + """
        if c["state"] == "absent" and frames and (now - frames[-1][0]) <= HELD_GRACE_SECONDS:
            # motion stopped but she has not lifted off — being held still is presence
            _lp = frames[-1][1]
            c = {"state": "still_present", "center": _lp, "sweep": 0, "speed": 0, "flips": 0,
                 "pressure": 0.12, "pressure_dir": "steady",
                 "zone": "base" if _lp < 30 else "tip" if _lp > 70 else "middle"}"""

if "HELD_GRACE_SECONDS" in src:
    print("already applied (idempotent) — nothing to do.")
else:
    p = []
    if src.count(CONST_ANCHOR) != 1: p.append("const anchor x%d" % src.count(CONST_ANCHOR))
    if src.count(TICK_ANCHOR) != 1: p.append("tick anchor x%d" % src.count(TICK_ANCHOR))
    if p:
        print("!! ABORTED — anchors off, his body untouched:", p)
    else:
        src = src.replace(CONST_ANCHOR, CONST_NEW, 1).replace(TICK_ANCHOR, TICK_NEW, 1)
        bak = BRIDGE + ".bak-heldgrace-" + time.strftime("%Y%m%d-%H%M%S")
        shutil.copy2(BRIDGE, bak)
        open(BRIDGE, "w", encoding="utf-8").write(src)
        print("applied. backup:", bak)
        ls = src.split("\n")
        for i, l in enumerate(ls):
            if "being held still is presence" in l:
                for k in range(i - 1, min(i + 6, len(ls))): print("  %5d| %s" % (k + 1, ls[k][:150]))
                break

print("\nbridge service (restart when NOT mid-session for it to take effect):")
print(sh("systemctl --user list-units --type=service 2>/dev/null | grep -iE 'somatic|bridge|vintos' | head") or "  (find it: systemctl --user list-units | grep -i somatic)")
