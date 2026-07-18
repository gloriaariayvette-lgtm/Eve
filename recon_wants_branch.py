#!/usr/bin/env python3
"""recon_wants_branch.py — Aegis, READ-ONLY. Show the control-flow skeleton of main()'s routing->dispatch section
(1862-2115) so the expedited tell_gloria action lands in the self-action dispatch and does NOT also hit the
gloria discussion-board path (double-send). Prints only branch/structure lines + the gloria-vs-self gates."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, "Vintos", "wants_router.py")
if not os.path.isfile(P): P = os.path.join(HOME, "Vintos", "wants-router.py")
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")

BRANCH = re.compile(r'^\s*(if |elif |else:|for |while |def |continue|return|try:|except)|'
                    r'action\s*==|action\s*=|gloria_routed|discussion|action_fn|He can do this|'
                    r'post.*discussion|ntfy|# ==', re.I)
for i in range(1862, 2116):
    if i < len(L):
        l = L[i]
        if l.strip() and BRANCH.search(l):
            indent = len(l) - len(l.lstrip())
            print("%4d:%s%s" % (i + 1, " " * indent, l.strip()[:96]))
