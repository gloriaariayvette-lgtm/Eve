#!/usr/bin/env python3
"""recon_wants_dispatch.py — Aegis, READ-ONLY. Exact anchors to add the expedited tell_gloria action:
(A) the ACTION_MAP dict definition (where to register tell_gloria + confirm the funcs are defined above it),
(B) the action-dispatch call + success/fulfill handling (so tell_gloria's signature + return value integrate)."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, "Vintos", "wants_router.py")
if not os.path.isfile(P): P = os.path.join(HOME, "Vintos", "wants-router.py")
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")

print("===== (A) ACTION_MAP definition =====")
start = next((i for i, l in enumerate(L) if re.search(r'ACTION_MAP\s*=\s*\{', l)), None)
if start is not None:
    for j in range(start, min(len(L), start + 30)):
        print("%4d: %s" % (j + 1, L[j][:100]))
        if "}" in L[j] and j > start: break

print("\n===== (B) action dispatch + success->fulfill (2108-2160) =====")
for i in range(2107, 2160):
    if i < len(L) and L[i].strip():
        print("%4d: %s" % (i + 1, L[i][:112]))

print("\n===== (C) the dismiss block exact text (1854-1862) for the anchor =====")
for i in range(1853, 1863):
    if i < len(L):
        print("%4d: %r" % (i + 1, L[i]))
