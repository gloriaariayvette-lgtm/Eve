#!/usr/bin/env python3
"""pinpoint.py — READ-ONLY, HARD-CAPPED (no flood). Only the exact chat-source lines in the 3 files
to fix: temporal, conversation-rhythm, and the outreach generator. Aegis."""
import os, re, glob
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")
HOME = os.path.expanduser("~")

def peek(path, pat, cap):
    if not os.path.isfile(path): return
    print(f"\n-- {path.replace(HOME,'~')} --")
    n = 0
    for i, l in enumerate(open(path, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(pat, l, re.I) and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:4}| {l.strip()[:140]}"); n += 1
            if n >= cap: break

print("=== 1) TEMPORAL — where 'last spoke' reads chat ===")
for f in sorted(set(glob.glob(os.path.join(SCRIPTS,"*temporal*"))+glob.glob(os.path.join(VIN,"*temporal*")))):
    if os.path.isfile(f) and not f.endswith(".pyc"):
        peek(f, r'chat-history|last.?spoke|last_msg|gloria|json\.load|avatar|voice|CHAT|days ago|open\(', 10)

print("\n=== 2) CONVERSATION-RHYTHM — the chat source ===")
peek(os.path.join(VIN,"conversation-rhythm.sh"), r'CHAT_HISTORY\s*=|chat-history|gloria_msgs\s*=|json\.load|avatar|voice', 8)

print("\n=== 3) OUTREACH generator — file + where its context/prompt is built ===")
og = []
for f in glob.glob(os.path.join(SCRIPTS,"*outreach*"))+glob.glob(os.path.join(SCRIPTS,"*initiate*"))+glob.glob(os.path.join(VIN,"*outreach*"))+glob.glob(os.path.join(VIN,"*initiate*")):
    if os.path.isfile(f) and not f.endswith(".pyc"): og.append(f)
print("  outreach files:", [f.replace(HOME,'~') for f in og] or "(none — searching for 'four days'/'silence' text producer)")
for f in og[:2]:
    peek(f, r'ledger|context|prompt|system|silence|chat-history|temporal|build|payload|content', 12)
