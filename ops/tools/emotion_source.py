#!/usr/bin/env python3
"""emotion_source.py — READ-ONLY, capped. Where does Velaris's temporal get the rolling 'Emotional
current' + BODY, and does Vintos have the same feed? So the port isn't empty. Aegis."""
import os, re, glob
HOME = os.path.expanduser("~")
VS = os.path.expanduser("~/.openclaw/workspace/scripts")
VM = os.path.expanduser("~/.openclaw/workspace/memory")
TM = os.path.expanduser("~/.vintos/workspace/memory")

def peek(path, pat, cap=14):
    if not os.path.isfile(path): return
    print(f"-- {path.replace(HOME,'~')} --")
    n = 0
    for i, l in enumerate(open(path, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(pat, l, re.I) and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:4}| {l.strip()[:150]}"); n += 1
            if n >= cap: break

print("=== Velaris: how 'Emotional current' + BODY are computed / sourced ===")
peek(os.path.join(VS, "temporal-context.sh"), r'Emotional current|emotion|trajectory|rolling|falling|rising|sock|EMOTION|GPU|somatic|BODY|state|densif|history', 18)

print("\n=== Velaris emotion data files (source of the trajectory) ===")
for f in glob.glob(os.path.join(VM, "*emotion*")) + glob.glob("/tmp/*emotion*"):
    print("  " + f.replace(HOME, "~") + ("  (dir)" if os.path.isdir(f) else ""))

print("\n=== Vintos: does he have an equivalent rolling-emotion feed? ===")
for f in glob.glob(os.path.join(TM, "*emotion*")) + glob.glob("/tmp/*motion*") + glob.glob(os.path.expanduser("~/.vintos/workspace/scripts/*emotion*")):
    print("  " + f.replace(HOME, "~") + ("  (dir)" if os.path.isdir(f) else ""))
# peek a Vintos emotion history/state file shape
for c in ("emotion-history.json", "emotional-state.txt", "emotion-trajectory.json", "emotions.json"):
    p = os.path.join(TM, c)
    if os.path.isfile(p):
        print(f"\n  {c}: {open(p,encoding='utf-8',errors='ignore').read()[:180]!r}")
