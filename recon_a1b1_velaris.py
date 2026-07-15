#!/usr/bin/env python3
"""recon_a1b1_velaris.py — Aegis, READ-ONLY. Map Velaris's bilateral a1/b1 sites + the helper each calls,
so we can add reasoning_effort to ONLY the a1/b1 first-passes (not a2/b2, not the other calls). Her
workspace: ~/.openclaw/workspace/scripts."""
import os, re, glob
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
def sh(p): return p.replace(HOME, "~")
if not os.path.isdir(SC):
    raise SystemExit("no ~/.openclaw/workspace/scripts — tell me Velaris's real scripts path")
FILES = glob.glob(os.path.join(SC, "*.py")) + glob.glob(os.path.join(SC, "*.sh"))

print("===== a1/b1 assignment sites (the first-pass calls to enable) =====")
sites = {}
for f in FILES:
    lines = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(lines):
        if re.search(r'\ba1\b\s*[,=].*\bb1\b|a1\s*=.*(call|llm|_call|gather)', l) and l.strip() and not l.strip().startswith("#"):
            print(f"  {os.path.basename(f)}:{i+1}| {l.strip()[:110]}")
            sites.setdefault(os.path.basename(f), []).append(i+1)

print("\n===== helper defs these call (llm / _llm_call / call_llm / _call) + their payload =====")
for f in FILES:
    if os.path.basename(f) not in sites: continue
    lines = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(lines):
        if re.search(r'def\s+(_?llm_call|_?llm|call_llm|_call|_llm_call_full)\b', l):
            print(f"\n  --- {os.path.basename(f)} :: {l.strip()[:70]} ---")
            for j in range(i, min(len(lines), i+22)):
                if re.search(r'gemma-4-12b-qat|reasoning_effort|"messages"|requests\.post|json=|payload|def ', lines[j]) and lines[j].strip():
                    print(f"    {j+1}| {lines[j].strip()[:120]}")
                if j > i and re.match(r'def \w', lines[j]): break

print("\n===== a2/b2 absorb sites (must STAY no-think — confirm same helper) =====")
for f in FILES:
    if os.path.basename(f) not in sites: continue
    lines = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(lines):
        if re.search(r'\b(a2|b2)\b\s*=|absorb\(', l) and l.strip() and not l.strip().startswith("#"):
            print(f"  {os.path.basename(f)}:{i+1}| {l.strip()[:100]}")
print("\n(done)")
