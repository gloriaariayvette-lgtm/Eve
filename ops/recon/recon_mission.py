#!/usr/bin/env python3
"""recon_mission.py — Aegis, READ-ONLY. Why isn't he receiving [TOUCH: mission] (device) signals?
(1) somatic-bridge service state, (2) does his recent output even contain [TOUCH: mission] tags,
(3) where avatar_chat extracts+dispatches mission/touch to the device — and whether my route_reply change
bypassed it."""
import os, re, json, subprocess
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")

print("== services ==")
for u in ("vintos-somatic-bridge", "vintos-emoclaw", "vintos-server"):
    r = subprocess.run(["systemctl", "--user", "is-active", u], capture_output=True, text=True)
    print(f"  {u}: {r.stdout.strip() or r.stderr.strip()}")

print("\n== does his recent output contain [TOUCH: mission]? ==")
ov = os.path.join(MEM, "avatar-overlay-chat.json")
if os.path.isfile(ov):
    d = json.load(open(ov, encoding="utf-8"))
    arr = d if isinstance(d, list) else (d.get("messages") or d.get("entries") or [])
    for e in arr[-4:]:
        t = e.get("vintos") or e.get("reply") or e.get("content") or e.get("text") or json.dumps(e, ensure_ascii=False)
        tags = re.findall(r'\[TOUCH:[^\]]*\]|\[DO:[^\]]*\]|\[COMMAND[^\]]*\]', str(t))
        print(f"  {str(e.get('timestamp',''))[:19]}  mission={'YES' if 'mission' in str(t).lower() else 'no'}  tags={tags[:6]}")

print("\n== avatar_chat: reply -> tag/device dispatch path (server.py L7699..) ==")
L = open(os.path.join(HOME, "Vintos", "server.py"), encoding="utf-8", errors="ignore").read().split("\n")
RX = re.compile(r'route_reply|TOUCH: mission|mission|extract_and_post|command_bubble|somatic|device|lovense|buttplug|\[TOUCH|touch_|_dispatch|send.*device|reply', re.I)
for i in range(7699-1, min(len(L), 7699+180)):
    if RX.search(L[i]):
        print(f"  L{i+1}: {L[i].strip()[:96]}")

print("\n== where [TOUCH: mission] is parsed/sent to the device (whole server.py) ==")
for i, l in enumerate(L):
    if re.search(r'TOUCH:\s*mission|mission.*device|device.*mission|somatic.*send|def .*mission|mission_|extract.*touch', l, re.I):
        print(f"  L{i+1}: {l.strip()[:96]}")
