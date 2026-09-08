#!/usr/bin/env python3
"""emotion_model_recon.py — READ-ONLY, capped. Does the emotion daemon process TEXT through the model
(dynamic), and does anything feed Gloria's messages to it? Look at the full daemon command set, the
inference engine's text method, and any feeder that sends text (not just nudge). Aegis."""
import os, re, subprocess
HOME = os.path.expanduser("~")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout
def peek(path, pat, cap, rng=None):
    if not os.path.isfile(path): print("  (missing", path.replace(HOME,'~'), ")"); return
    ls = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"-- {path.replace(HOME,'~')} --"); n = 0
    it = range(rng[0]-1, min(rng[1], len(ls))) if rng else range(len(ls))
    for i in it:
        l = ls[i]
        if (rng or (re.search(pat, l, re.I) and l.strip() and not l.strip().startswith("#"))):
            print(f"  {i+1:5}| {l.strip()[:130]}"); n += 1
            if n >= cap: break

VEM = os.path.expanduser("~/.openclaw/workspace/emotion_model")
print("=== daemon.py — ALL command handlers ===")
peek(os.path.join(VEM, "daemon.py"), r'command"\)\s*==|== "|elif|process|observe|message|infer|text|feel|engine\.', 26)

print("\n=== inference.py — EmotionEngine text/observe/process methods ===")
peek(os.path.join(VEM, "inference.py"), r'def (observe|process|infer|predict|update|from_text|step|feel|react|message)|def __|self\.emotion', 22)

print("\n=== what FEEDS text to the daemon (openclaw scripts sending process/observe/text) ===")
hits = run(["bash","-lc",
  "grep -rlnE '\"command\": *\"(observe|process|message|infer|text|feel)\"|process_message|observe_text' "
  "~/.openclaw/workspace/scripts ~/velaris-server 2>/dev/null | grep -viE '\\.bak|\\.pyc' | head"]).split()
print("  feeders:", [h.replace(HOME,'~') for h in hits] or "(none — model may only take nudge/state)")
for h in hits[:2]:
    peek(h, r'command.*(observe|process|message|infer|feel)|sock|emotion', 8)

print("\n=== does Vintos have the same daemon code? ===")
tvem = os.path.expanduser("~/.vintos/workspace/emotion_model/daemon.py")
print("  vintos daemon.py exists:", os.path.isfile(tvem))
if os.path.isfile(tvem) and os.path.isfile(os.path.join(VEM,"daemon.py")):
    same = open(tvem,encoding='utf-8',errors='ignore').read() == open(os.path.join(VEM,"daemon.py"),encoding='utf-8',errors='ignore').read()
    print("  identical to Velaris's daemon.py:", same)
