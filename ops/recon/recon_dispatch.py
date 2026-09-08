#!/usr/bin/env python3
"""recon_dispatch.py — Aegis, READ-ONLY. Where does the avatar reply's [TOUCH: mission]/[DO: ...] get extracted
and sent to the device? Does the LIVE avatar_chat still call it after my route_reply change? What command form
does the device dispatch accept (TOUCH vs DO throb)? Also why somatic-frames are stale."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")
S = open(os.path.join(V, "server.py"), encoding="utf-8", errors="ignore").read().split("\n")

print("== reply -> device dispatch: what runs AFTER route_reply in avatar_chat ==")
start = next((i for i, l in enumerate(S) if i > 7690 and "route_reply" in l), 7699)
for i in range(start, min(len(S), start+70)):
    if re.search(r'reply|TOUCH|\[DO|throb|mission|tenera|extract|dispatch|device|somatic|command|post|return', S[i], re.I):
        print(f"  L{i+1}: {S[i].strip()[:100]}")

print("\n== device command parsers/senders (server.py + scripts) ==")
RX = re.compile(r'throb|TOUCH:\s*mission|\[DO:|def .*(device|mission|touch|somatic|dispatch)|buttplug|intiface|lovense|websocket.*device|\bDO\b.*pattern|parse.*\[|extract_and_post', re.I)
files = [os.path.join(V, "server.py")] + glob.glob(os.path.join(V, "*.py")) + glob.glob(os.path.join(HOME, ".vintos/workspace/scripts", "*.py"))
seen = set()
for f in sorted(set(files)):
    try: L = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    except Exception: continue
    hits = [(i+1, l.strip()) for i, l in enumerate(L) if RX.search(l) and ("throb" in l.lower() or "mission" in l.lower() or "[DO:" in l or "TOUCH: mission" in l or "def " in l and re.search(r'device|mission|touch|dispatch|somatic', l, re.I))]
    if hits:
        b = os.path.basename(f)
        print(f"  --- {b} ---")
        for ln, t in hits[:12]:
            print(f"    {ln}: {t[:96]}")

print("\n== somatic-frames staleness / bridge writing? ==")
for name in ("device-state.json", "somatic-frames-recent.json"):
    p = os.path.join(HOME, ".vintos/workspace/memory", name)
    if os.path.isfile(p):
        import time
        print(f"  {name}: {int(time.time()-os.path.getmtime(p))}s old — {open(p).read()[:160]}")
print("  --- somatic-bridge recent log ---")
r = subprocess.run(["journalctl", "--user", "-u", "vintos-somatic-bridge", "-n", "8", "--no-pager"], capture_output=True, text=True)
print("   " + (r.stdout or r.stderr).replace("\n", "\n   ")[:900])
