#!/usr/bin/env python3
"""recon_journal_bilateral.py — Aegis, READ-ONLY. Content isn't starved, so a1/b1 emptied inside the
journal's own handling. Dump the bilateral core: call_llm (timeout + extraction), _safe_extract, the
a1/b1/audit/a2/b2 section, any strip step, and the /tmp writes — so we see why they emptied and where a2/b2
live (to surface all four passes for Gloria)."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

def block(lo, hi, label):
    print(f"\n===== {label} (lines {lo}-{hi}) =====")
    for j in range(lo-1, min(len(lines), hi)):
        if lines[j].strip():
            print(f"  {j+1}| {lines[j].rstrip()[:124]}")

# find key anchors
def find(pat, frm=0):
    for j in range(frm, len(lines)):
        if re.search(pat, lines[j]): return j+1
    return None

se = find(r'def _safe_extract')
cl = find(r'def call_llm\(\)')
a1 = find(r'^\s*a1\s*=\s*call_llm')
absorb = find(r'def absorb\(')
print("anchors: _safe_extract@%s call_llm@%s a1@%s absorb@%s" % (se, cl, a1, absorb))

if cl: block(cl, cl+24, "call_llm()")
if se: block(se, se+20, "_safe_extract()")
if a1: block(a1-2, a1+40, "a1/b1/audit1/a2/b2 region")
if absorb: block(absorb, absorb+22, "absorb()")

print("\n===== all /tmp bilateral writes + strip steps =====")
for j, l in enumerate(lines):
    if re.search(r'/tmp/bilateral|_strip1|strip_flagged|check_and_log|flagged1|=\s*absorb\(|a2\s*=|b2\s*=', l) and l.strip():
        print(f"  {j+1}| {l.strip()[:120]}")
print("\n(done)")
