#!/usr/bin/env python3
"""recon_velaris_chat.py — Aegis, READ-ONLY. Her chat IS bilateral; my earlier regex missed it. Find her
chat server + its a1/b1 block in ANY form (separate-line assigns, different helper name, threaded), and dump
the helper it calls so we can add reasoning_effort to the chat a1/b1 first-pass too."""
import os, re, glob
HOME = os.path.expanduser("~")
OC = os.path.join(HOME, ".openclaw")
def sh(p): return p.replace(HOME, "~")

# locate server-ish files
cands = []
for f in glob.glob(os.path.join(OC, "**", "*.py"), recursive=True):
    if "backup" in f or "/scripts/" in f:
        # still allow scripts, but prioritize server
        pass
    try: txt = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    score = 0
    if re.search(r'bilateral', txt, re.I): score += 2
    if re.search(r'/tmp/bilateral|bilateral-chat|velaris-bilateral', txt): score += 2
    if re.search(r'\ba1\b', txt) and re.search(r'\bb1\b', txt): score += 1
    if re.search(r'8400|FastAPI|uvicorn|@app\.(post|get)', txt): score += 1
    if score >= 3:
        cands.append((score, f, txt))
cands.sort(reverse=True)
print("===== candidate chat/bilateral files (by score) =====")
for score, f, _ in cands[:8]:
    print(f"  [{score}] {sh(f)}")

# for the top file(s), dump the bilateral block + helper
for score, f, txt in cands[:3]:
    lines = txt.split("\n")
    print(f"\n===== {sh(f)} — bilateral a1/b1 region =====")
    hot = [i for i, l in enumerate(lines) if re.search(r'\b(a1|b1)\b|bilateral|_llm_call|absorb|reasoning_effort|gemma-4-12b-qat', l)]
    shown = set()
    for i in hot:
        for j in range(max(0, i-1), min(len(lines), i+2)):
            if j in shown or not lines[j].strip(): continue
            shown.add(j)
            print(f"  {j+1}| {lines[j].strip()[:118]}")
        if len(shown) > 60: print("  … (truncated)"); break
print("\n(done — point me at the chat a1/b1 call + its helper)")
