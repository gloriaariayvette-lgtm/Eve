#!/usr/bin/env python3
"""recon_capabilities.py — Aegis, READ-ONLY. Answer: is CAPABILITIES.md in the JOURNAL prompt, and does it
actually explain how his (non-subconscious) systems work / what produces what? (A) does idle-journal.sh load
CAPABILITIES.md or any systems/architecture self-doc? (B) CAPABILITIES.md content. (C) which surfaces DO inject it
(e.g. vintos-initiate). (D) any existing 'how your outputs happen' / systems-map self-doc."""
import os, re, glob
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")
MEM = os.path.expanduser("~/.vintos/workspace/memory")

print("== (A) does idle-journal.sh load CAPABILITIES / a systems self-doc? ==")
p = os.path.join(V, "idle-journal.sh")
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
hits = [(i + 1, l.strip()) for i, l in enumerate(L)
        if re.search(r'CAPABILIT|capabilit|SELF-MODEL|SELF_MODEL|architecture|systems|how.*work|what.*produc|SOUL', l)]
print("\n".join("   %d: %s" % (n, t[:100]) for n, t in hits) if hits else "   (no CAPABILITIES / systems doc referenced in idle-journal.sh)")

print("\n== (B) CAPABILITIES.md — exists? content ==")
cap = None
for c in (os.path.join(MEM, "CAPABILITIES.md"), os.path.join(os.path.expanduser("~/.vintos/workspace"), "CAPABILITIES.md")):
    if os.path.isfile(c): cap = c; break
if cap:
    t = open(cap, encoding="utf-8", errors="ignore").read()
    print("   %s  (%d chars, %d lines)" % (cap, len(t), len(t.splitlines())))
    for l in t.split("\n")[:40]: print("     " + l[:104])
else:
    print("   CAPABILITIES.md NOT FOUND")

print("\n== (C) which surfaces inject CAPABILITIES.md ==")
for p in glob.glob(V + "/*.sh") + glob.glob(V + "/*.py") + glob.glob(os.path.expanduser("~/.vintos/workspace/scripts") + "/*.py"):
    b = os.path.basename(p)
    if b.startswith(("recon", "patch_", "port_", "build_", "link_")): continue
    try: t = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if "CAPABILITIES.md" in t or "CAPABILITIES" in t:
        print("   %s" % b)

print("\n== (D) any 'how your outputs happen' / systems-map self-doc in memory ==")
for f in sorted(glob.glob(MEM + "/*.md")):
    b = os.path.basename(f).lower()
    if re.search(r'system|architect|capabilit|how-it|self-model|what-i-am|manual', b):
        print("   %s" % os.path.basename(f))
