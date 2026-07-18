#!/usr/bin/env python3
"""recon_introspection_call.py — Aegis, READ-ONLY, FAST (specific files only, no walk). The discovery ritual is
introspection -> Opus. Copy the EXACT call shape his existing introspection jobs use, and how they resolve the
model (no hardcoded id). Show: the shim's CLAUDE_MODEL + port, and the requests.post/model lines in the pinned
introspection jobs (taste-reflection, ambition-check). Also how the Gemma path looks (for her, later). Nothing written."""
import os, re
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")

def show(path, rx, tag, cap=112, lim=18):
    if not (os.path.isfile(path) or os.path.islink(path)):
        print("  %s: (not found)" % tag); return
    L = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    hits = [(i + 1, l) for i, l in enumerate(L) if re.search(rx, l)]
    print("  %s: %s" % (tag, path))
    for i, l in hits[:lim]:
        print("     %4d: %s" % (i, l.strip()[:cap]))
    if not hits: print("     (no matches)")

print("== shim: port + CLAUDE_MODEL (how Opus is named without hardcoding an id) ==")
for name in ("vintos_claude_shim.py", "vintos-claude-shim.py"):
    p = os.path.join(HIS, name)
    if not os.path.isfile(p): p = os.path.join(VIN, name)
    show(p, r'CLAUDE_MODEL|8599|def .*complete|host=|port=|route|/v1/chat|model', "shim")

print("\n== introspection jobs — the LLM POST + model resolution to copy ==")
for name in ("taste-reflection.py", "taste_reflection.py", "ambition-check.py", "ambition_check.py"):
    for base in (VIN, HIS):
        p = os.path.join(base, name)
        if os.path.isfile(p) or os.path.islink(p):
            show(p, r'requests\.post|http://127|:8599|:1234|"model"|MODEL\s*=|CLAUDE_MODEL|chat/completions|8500|shim', name)
            break

print("\n== how idle-journal invokes its model (bash -> python/curl) ==")
for name in ("idle-journal.sh", "vintos-initiate.sh"):
    p = os.path.join(VIN, name)
    show(p, r'8599|1234|curl|python3|MODEL|shim|chat/completions', name, lim=10)

print("\n(READ-ONLY. Gives the exact introspection call shape for the discovery ritual's Opus reflection.)")
