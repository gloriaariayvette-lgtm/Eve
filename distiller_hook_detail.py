#!/usr/bin/env python3
"""distiller_hook_detail.py — READ-ONLY. Her 3 distiller hook blocks verbatim (with context) + the
matching anchors in HIS server, so his post-response hooks mirror hers exactly and insert at the right
spots. Fresh name.
"""
import os, re

HOME = os.path.expanduser("~")
HER = os.path.expanduser("~/velaris-server/server.py")
HIS = os.path.expanduser("~/Vintos/server.py")

her = open(HER, encoding="utf-8", errors="ignore").read().splitlines() if os.path.exists(HER) else []
his = open(HIS, encoding="utf-8", errors="ignore").read().splitlines() if os.path.exists(HIS) else []

# her hook regions (1-indexed comment lines seen in recon): 3363, 7925, 13681
REGIONS = [(3358, 3382), (7920, 7952), (13676, 13700)]

print("=== HER distiller hook blocks (verbatim, to mirror) ===")
for lo, hi in REGIONS:
    print("\n-- her lines %d-%d --" % (lo, hi))
    for i in range(lo - 1, min(hi, len(her))):
        s = her[i].rstrip()
        if s.strip():
            print("  %5d: %s" % (i + 1, s[:160]))

print("\n\n=== HIS server: does the distiller already appear? + matching anchors ===")
ed_hits = [i + 1 for i, ln in enumerate(his) if re.search(r'enactment', ln, re.I)]
print("  enactment refs in his server: %s" % (ed_hits or "NONE (hook absent — will add)"))

# For each her-hook, grab the line just ABOVE the enactment comment as an anchor, find it in his server.
print("\n-- anchor search (find where to insert in his server) --")
for lo, hi in REGIONS:
    # the anchor = first non-enactment, non-blank code line above the region's comment
    anchor = None
    for i in range(lo - 2, max(0, lo - 12), -1):
        s = her[i].strip()
        if s and "enactment" not in s.lower() and not s.startswith("#"):
            anchor = s; anchor_ln = i + 1; break
    if not anchor:
        print("  region %d: no clean anchor found" % lo); continue
    # find that anchor in his server
    matches = [j + 1 for j, ln in enumerate(his) if ln.strip()[:60] == anchor[:60]]
    print("  her@%d anchor: %r" % (anchor_ln, anchor[:80]))
    print("     -> his server line(s): %s" % (matches[:6] or "NOT FOUND (structure diverged here)"))
print("\n=== done ===")
