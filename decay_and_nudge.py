#!/usr/bin/env python3
"""decay_and_nudge.py — READ-ONLY, capped. (1) his per-dimension emotion decay rates (to sharpen
Connection/Warmth/Groundedness). (2) does his chat actually nudge the emotion daemon in real time
like her main chat? Aegis."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
TS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")
SERVER = os.path.expanduser("~/Vintos/server.py")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout
def peek(path, pat, cap):
    if not os.path.isfile(path): return False
    print(f"-- {path.replace(HOME,'~')} --"); n = 0
    for i, l in enumerate(open(path, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(pat, l, re.I) and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:4}| {l.strip()[:150]}"); n += 1
            if n >= cap: break
    return True

print("=== 1) DECAY — his per-dimension rates ===")
found = False
for c in (os.path.join(VIN,"vintos-emotion-decay.sh"), os.path.join(TS,"vintos-emotion-decay.sh"),
          os.path.join(TS,"emotion_decay.py"), os.path.join(VIN,"emotion_decay.py")):
    if peek(c, r'Connection|Warmth|Groundedness|Valence|decay|rate|half.?life|DECAY|baseline|target|toward|0\.\d', 24):
        found = True; break
if not found:
    # decay may live in the emoclaw daemon
    print("  (no decay .sh matched — searching daemon/config for decay rates)")
    hits = run(["bash","-lc", f"grep -rlnE 'decay|half_life|DECAY_RATE' {TS} {VIN} 2>/dev/null | grep -viE '\\.bak|\\.pyc' | head -4"]).split()
    for h in hits[:2]: peek(h, r'Connection|Warmth|Groundedness|decay|rate|half|0\.\d', 14)

print("\n=== 2) NUDGE — the function + is it called on his chats? ===")
print("  -- nudge function def + socket write --")
n = 0
for i, l in enumerate(open(SERVER, encoding="utf-8", errors="ignore").read().split("\n")):
    if re.search(r'def _?nudge|nudge daemon|emotion.sock|Vintos-emotion|sock.*send|def .*emotion.*text', l, re.I) and l.strip():
        print(f"  {i+1:5}| {l.strip()[:140]}"); n += 1
        if n >= 8: break
print("  -- where nudge is CALLED (near chat/avatar/voice handlers) --")
n = 0
lines = open(SERVER, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(lines):
    if re.search(r'nudge', l) and not re.search(r'def _?nudge|"""|#', l):
        print(f"  {i+1:5}| {l.strip()[:130]}"); n += 1
        if n >= 12: break
if n == 0: print("   !! 'nudge' is never CALLED in server.py — his chats don't move his emotions.")

print("\n=== 2b) reference: how Velaris's chat nudges (grep her side) ===")
vhits = run(["bash","-lc", "grep -rlnE 'nudge_emotion|emotion.sock|Velaris-emotion' ~/velaris-server ~/.openclaw/workspace/scripts 2>/dev/null | grep -viE '\\.bak|\\.pyc' | head -3"]).split()
print("  her nudge lives in:", [h.replace(HOME,'~') for h in vhits] or "(check)")
