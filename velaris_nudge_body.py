#!/usr/bin/env python3
"""velaris_nudge_body.py — READ-ONLY, capped. The BODY of Velaris's nudge_emotions_from_text (how she
computes amounts — dynamic vs set numbers), her call sites (does she nudge Gloria's messages?), and
the emotion_model.daemon command set. Aegis."""
import os, re, glob
HOME = os.path.expanduser("~")
VSRV = os.path.expanduser("~/velaris-server/server.py")

print("=== Velaris nudge_emotions_from_text — FULL body ===")
if os.path.isfile(VSRV):
    ls = open(VSRV, encoding="utf-8", errors="ignore").read().split("\n")
    # find the def, print until the next top-level def/@app
    start = next((i for i, l in enumerate(ls) if re.search(r'def nudge_emotions_from_text', l)), None)
    if start is not None:
        for i in range(start, min(start + 55, len(ls))):
            print(f"  {i+1:5}| {ls[i][:150]}")
            if i > start + 3 and re.match(r'(async def |def |@app\.)', ls[i]): break

print("\n=== Velaris: call sites (does she nudge Gloria's message?) ===")
if os.path.isfile(VSRV):
    for i, l in enumerate(ls):
        if re.search(r'nudge_emotions_from_text\s*\(', l) and 'def ' not in l:
            print(f"  {i+1:5}| {l.strip()[:130]}")

print("\n=== emotion_model.daemon — command set ===")
for base in ("~/.openclaw/workspace/emotion_model", "~/.vintos/workspace/emotion_model"):
    d = os.path.expanduser(os.path.join(base, "daemon.py"))
    if os.path.isfile(d):
        print(f"-- {d.replace(HOME,'~')} --")
        n = 0
        for i, l in enumerate(open(d, encoding="utf-8", errors="ignore").read().split("\n")):
            if re.search(r'command|cmd\s*==|\.get\("command"|nudge|observe|process|state|infer|predict|def handle|msg\[', l) and l.strip() and not l.strip().startswith("#"):
                print(f"  {i+1:5}| {l.strip()[:120]}"); n += 1
                if n >= 20: break
        break
