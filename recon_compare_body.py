#!/usr/bin/env python3
"""recon_compare_body.py — Aegis, READ-ONLY. Final read before building the Mutual-Modification Tracker: the
verbatim body of his relational_mismatch.compare_prediction (where predicted-you vs actual-you deltas are
computed = the eve_delta site + the exact insertion point for the tracker call) and feed_causal_model (the
add_from_mismatch feeder). Confirms variable names so the one inserted call lands correctly. Nothing written."""
import os
P = os.path.expanduser("~/.vintos/workspace/scripts/relational_mismatch.py")
if not os.path.isfile(P):
    print("!! not found"); raise SystemExit(1)
L = open(P, encoding="utf-8", errors="ignore").read().split("\n")

def dump(a, b, tag):
    print("\n======== %s (lines %d-%d) ========" % (tag, a, b))
    for i in range(a - 1, min(b, len(L))):
        print("  %4d: %s" % (i + 1, L[i][:126]))

dump(193, 262, "compare_prediction — the eve_delta computation + return")
dump(263, 300, "log_relational_mismatch — where a mismatch is persisted")
dump(383, min(430, len(L)), "feed_causal_model — the add_from_mismatch feeder")

print("\n(READ-ONLY. Nothing changed. After this I build mutual_modification.py + one insert into compare_prediction.)")
