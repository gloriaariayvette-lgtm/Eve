#!/usr/bin/env python3
"""recon_a1b1_velaris2.py — Aegis, READ-ONLY. Close the gaps before patching Velaris a1/b1:
(1) find her chat SERVER's bilateral block (search ~/.openclaw broadly), (2) usage counts of llm()/call_llm()
in value-map + idle-journal (a1/b1-only, or shared with synthesis/audit?), (3) introspection first-pass
thread setup so we can gate call_llm by a reason flag."""
import os, re, glob
HOME = os.path.expanduser("~")
OC = os.path.join(HOME, ".openclaw")
SC = os.path.join(OC, "workspace/scripts")
def sh(p): return p.replace(HOME, "~")

print("===== (1) Velaris chat server bilateral block (a1,b1 = ... gather/_llm_call) =====")
serv = []
for f in glob.glob(os.path.join(OC, "**", "*.py"), recursive=True):
    if "backup" in f or "/scripts/" in f and os.path.basename(f) != "server.py":
        pass
    try: txt = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if re.search(r'a1,\s*b1\s*=.*(gather|_llm_call)', txt):
        serv.append(f)
for f in sorted(set(serv)):
    print("  FOUND:", sh(f))
    lines = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(lines):
        if re.search(r'a1,\s*b1\s*=|def _llm_call|_absorb_|reasoning_effort|_llm_call\(', l) and l.strip():
            print(f"    {i+1}| {l.strip()[:115]}")
if not serv: print("  (none found — her chat may not be bilateral, or server path differs)")

def count_calls(path, fn):
    if not os.path.isfile(path): print(f"  {sh(path)} MISSING"); return
    lines = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"\n  {os.path.basename(path)} — every '{fn}(' call:")
    for i, l in enumerate(lines):
        if re.search(r'(?<![\w])' + re.escape(fn) + r'\s*\(', l) and l.strip() and 'def ' + fn not in l:
            print(f"    {i+1}| {l.strip()[:100]}")

print("\n===== (2) usage counts — is the helper a1/b1-only or shared? =====")
count_calls(os.path.join(SC, "value-map.py"), "llm")
count_calls(os.path.join(SC, "idle-journal.sh"), "call_llm")

print("\n===== (3) introspection first-pass thread setup (lines 400-420) =====")
p = os.path.join(SC, "introspection.sh")
if os.path.isfile(p):
    lines = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    for j in range(399, min(len(lines), 420)):
        if lines[j].strip(): print(f"    {j+1}| {lines[j].strip()[:115]}")
print("\n(done)")
