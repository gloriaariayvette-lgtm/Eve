#!/usr/bin/env python3
"""recon_introspection.py — Aegis, READ-ONLY, terse. Structure needed to apply the reasoning recipe to
introspection a1/b1 only: call_llm payload, run(), the first-pass thread creations (t1/t2) vs absorb threads,
system/base_msgs assembly, and rule/constraint lines to strip."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")
def show(lbl, pat, cap=8):
    print(f"-- {lbl} --"); n = 0
    for i, l in enumerate(L):
        if re.search(pat, l) and l.strip():
            print(f"{i+1}: {l.strip()[:96]}"); n += 1
            if n >= cap: break
show("call_llm def + model/max_tokens", r'def call_llm|gemma-4-12b-qat|max_tokens|payload = json|reasoning_effort', 6)
show("run def + call", r'def run\(|results\[i\] = call_llm|call_llm\(msgs', 4)
show("thread creations (first-pass vs absorb)", r'threading\.Thread\(target=run|Thread\(target=run', 8)
show("base_msgs / system assembly", r'base_msgs|system\s*=|\{.role.:\s*.system|system_msg', 6)
show("rule/constraint lines", r"BANNED|HARD BAN|forbidden|ABSOLUTE RULES|DO NOT|Do NOT|do not repeat", 10)
