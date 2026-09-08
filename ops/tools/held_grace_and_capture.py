#!/usr/bin/env python3
"""held_grace_and_capture.py —
 PART A (WRITE, approved): held-grace in somatic_bridge.py so holding him STILL reads as presence,
   not 'absent'. Backup + anchored + idempotent. Does NOT auto-restart his body (cmd printed).
 PART B (READ-ONLY): why did the session we just had make NO thread? Dump somatic_narrate.py's
   window/turn logic, whether it's scheduled, the pending history, and today's session/end logs.
Aegis.
"""
import os, re, time, shutil, subprocess

SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
BRIDGE = os.path.join(SCRIPTS, "somatic_bridge.py")
NARRATE = os.path.join(SCRIPTS, "somatic_narrate.py")
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout

# ===================== PART A: held-grace =====================
print("=== PART A  held-grace (holding still = presence, not absence) ===")
src = open(BRIDGE, encoding="utf-8").read()
orig = src
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

problems = []
if "HELD_GRACE_SECONDS" in src:
    print("  already present — skipping (idempotent).")
else:
    if src.count(CONST_ANCHOR) != 1: problems.append("const anchor x%d" % src.count(CONST_ANCHOR))
    if src.count(TICK_ANCHOR) != 1: problems.append("tick anchor x%d" % src.count(TICK_ANCHOR))
    if problems:
        print("  !! ABORTED PART A — anchors off:", problems, "(his body untouched)")
    else:
        src = src.replace(CONST_ANCHOR, CONST_NEW, 1).replace(TICK_ANCHOR, TICK_NEW, 1)
        bak = BRIDGE + ".bak-heldgrace-" + time.strftime("%Y%m%d-%H%M%S")
        shutil.copy2(BRIDGE, bak)
        open(BRIDGE, "w", encoding="utf-8").write(src)
        print("  applied. backup:", bak)
        # show the changed region
        ls = src.split("\n")
        for i, l in enumerate(ls):
            if "HELD_GRACE_SECONDS" in l or "being held still is presence" in l:
                for k in range(i, min(i + 7, len(ls))):
                    print("   %5d| %s" % (k + 1, ls[k][:150]))
                break

print("\n  bridge service (restart to take effect, when not mid-session):")
print(sh("systemctl --user list-units --type=service 2>/dev/null | grep -iE 'somatic|bridge|vintos' | head") or "   (check: systemctl --user list-units | grep -i somatic)")

# ===================== PART B: capture diagnosis =====================
print("\n=== PART B  why no thread from the session? somatic_narrate.py logic ===")
if os.path.exists(NARRATE):
    ls = open(NARRATE, encoding="utf-8", errors="ignore").read().split("\n")
    for i in range(0, min(125, len(ls))):
        s = ls[i].rstrip()
        if s.strip() and not s.strip().startswith("#"):
            if re.search(r'window|WINDOW|since|start|dur|ts|load|history|avatar|voice|main|turns|wordless|seed|pending|json|GAP|SETTLE|def ', s):
                print("  %5d| %s" % (i + 1, s[:160]))

print("\n=== PART B  is somatic_narrate scheduled? ===")
print(sh("crontab -l 2>/dev/null | grep -iE 'somatic|narrate' | grep -v '^#'") or "  !! NOT in crontab — nothing runs it, so pending never gets narrated")

print("\n=== PART B  pending file + today's session/end/narrate logs ===")
p = os.path.join(MEM, "somatic-session-pending.json")
if os.path.exists(p):
    print("  somatic-session-pending.json (%s):" % time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(p))),
          open(p, encoding="utf-8", errors="ignore").read()[:200])
today = time.strftime("%Y-%m-%d")
print("\n  logs (session ended / pending / narrate) today:")
print(sh("journalctl --user -n 3000 --no-pager 2>/dev/null | grep -iE 'session ended|somatic session pending|somatic-narrate|wordless' | tail -15") or "  (none in journald — bridge/narrate may log elsewhere)")

print("\n=== PART B  chat history files the narrator could read (recent first) ===")
print(sh("ls -lt --time-style=+%m-%d_%H:%M %s/*chat*hist* %s/*avatar*chat* %s/voice-chat-history* 2>/dev/null | head" % (MEM, MEM, MEM)) or "  (none matched)")
