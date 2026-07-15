#!/usr/bin/env python3
"""recon_journal_result.py — Aegis, READ-ONLY. Show what the just-run journal produced: the newest journal
entry + the raw a1/b1 drafts (/tmp/bilateral-a1.txt,b1.txt), and flag any reasoning/think leakage into them."""
import os, re, glob
HOME = os.path.expanduser("~")
JDIR = os.path.join(HOME, ".openclaw/workspace/memory/journal")

def leak(s):
    tags = [x for x in ("<think>", "</think>", "channel|>", "|channel>", "<|channel", "reasoning") if x in s]
    return ("LEAK: " + ", ".join(tags)) if tags else "clean (no think-tags)"

# newest journal file + its last entry
files = sorted(glob.glob(os.path.join(JDIR, "*.md")), key=os.path.getmtime)
if files:
    f = files[-1]
    print("=== newest journal:", f.replace(HOME, "~"), "===")
    txt = open(f, encoding="utf-8", errors="ignore").read()
    entries = re.split(r'\n(?=## )', txt)
    last = entries[-1].strip()
    print(last[:1400])
    print("\n  -> entry", leak(last))
else:
    print("no journal file yet in", JDIR.replace(HOME, "~"))

for name in ("/tmp/bilateral-a1.txt", "/tmp/bilateral-b1.txt"):
    print("\n=== " + name + " (raw first-pass draft) ===")
    if os.path.isfile(name):
        s = open(name, encoding="utf-8", errors="ignore").read()
        print(s[:700])
        print("\n  ->", leak(s), f"| {len(s)} chars")
    else:
        print("  (missing)")
print("\n(done — drafts + journal should be clean prose; reasoning stayed server-side in reasoning_content)")
