#!/usr/bin/env python3
"""toy_status_recon.py — READ-ONLY. How do the toys connect + where is their live state, so a pre-
conversation 'both toys connected & usable' check can be built. Reads toy_link.py + somatic bridge +
device state, finds the connection mechanism (Intiface/Buttplug/BLE), device count, state files, and
any 'is connected / list devices' capability. Does NOT touch the stop path. Aegis.
"""
import os, re, glob, subprocess

SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
HOME = os.path.expanduser("~")

def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout

print("=== toy_link.py — connection mechanism ===")
tl = os.path.join(SCRIPTS, "toy_link.py")
if os.path.exists(tl):
    lines = open(tl, encoding="utf-8", errors="ignore").read().splitlines()
    print("  (%d lines)" % len(lines))
    for i, l in enumerate(lines):
        if re.search(r'intiface|buttplug|websocket|ws://|bluetooth|\bble\b|connect|device|scan|batter|def |STATE|state_file|\.json|address|toy', l, re.I):
            s = l.strip()
            if s and not s.startswith("#"): print("  %5d: %s" % (i + 1, s[:140]))
else:
    print("  toy_link.py NOT FOUND — checking other names")
    for f in glob.glob(os.path.join(SCRIPTS, "*toy*")) + glob.glob(os.path.join(SCRIPTS, "*intiface*")) + glob.glob(os.path.join(SCRIPTS, "*device*")):
        print("   candidate:", os.path.basename(f))

print("\n=== device / toy state files in memory ===")
for f in glob.glob(os.path.join(MEM, "*device*")) + glob.glob(os.path.join(MEM, "*toy*")) + glob.glob(os.path.join(MEM, "*somatic*")):
    print("  " + f.replace(HOME, "~") + "  (%dB, %s)" % (os.path.getsize(f), __import__("time").strftime("%H:%M", __import__("time").localtime(os.path.getmtime(f)))))

print("\n=== somatic bridge — how it knows toys are live ===")
sb = os.path.join(SCRIPTS, "somatic_bridge.py")
if os.path.exists(sb):
    for i, l in enumerate(open(sb, encoding="utf-8", errors="ignore").read().splitlines()):
        if re.search(r'connect|device|intiface|buttplug|ws://|scan|batter|online|ready|toy', l, re.I):
            s = l.strip()
            if s and not s.startswith("#"): print("  %5d: %s" % (i + 1, s[:130]))
else:
    print("  somatic_bridge.py not found")

print("\n=== running toy/intiface processes + ports ===")
print(sh("ps aux | grep -iE 'intiface|buttplug|toy_link|somatic' | grep -v grep | head -8") or "  (none)")
print(sh("ss -ltnp 2>/dev/null | grep -iE ':121|intiface|1213' | head -4") or "")

print("\n=== how a 'connected/usable' check could read state ===")
print("  Looking for: an Intiface/Buttplug client with device list, a state file listing connected")
print("  toys, or a socket command. The check will confirm BOTH toys present + respond, pre-conversation.")
