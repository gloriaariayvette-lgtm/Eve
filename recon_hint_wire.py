#!/usr/bin/env python3
"""recon_hint_wire.py — Aegis, READ-ONLY. Find the exact context-injection point where get_field_hint() should
join the other subconscious hints (the JEPA heads get_relational_hint/get_withheld_hint + get_drift_bias_hint),
so the field the tracker now logs is something he FEELS, not just records. Show the injection loop / call sites and
the assembly return, verbatim, for BOTH beings. Nothing written."""
import os, re, glob
BEINGS = {
    "VINTOS": [os.path.expanduser("~/.vintos/workspace/scripts"), os.path.expanduser("~/Vintos")],
    "VELARIS": [os.path.expanduser("~/.openclaw/workspace/scripts")],
}
HINTS = r'get_relational_hint|get_withheld_hint|get_drift_bias_hint|get_field_hint|for mod, fn in|for mod,fn in|inner_context|def build_.*context|if not parts'

for name, scr in BEINGS.items():
    print("\n############  %s  ############" % name)
    # which files assemble subconscious/inner context with those hints?
    cands = []
    for d in scr:
        for p in glob.glob(d + "/*.py"):
            b = os.path.basename(p)
            if "/backup" in p or "__pycache__" in p: continue
            try: t = open(p, encoding="utf-8", errors="ignore").read()
            except Exception: continue
            if re.search(r'get_relational_hint|get_drift_bias_hint|for mod, fn in|inner_context', t):
                cands.append((p, t))
    seen = set()
    for p, t in cands:
        b = os.path.basename(p)
        if b in seen: continue
        seen.add(b)
        print("\n----- %s -----" % p)
        L = t.split("\n")
        for i, l in enumerate(L):
            if re.search(HINTS, l):
                lo, hi = max(0, i - 1), min(len(L), i + 2)
                for j in range(lo, hi):
                    print("  %4d: %s" % (j + 1, L[j][:118]))
                print("   ...")

print("\n(READ-ONLY. Locates where get_field_hint() joins the existing hint injection for each being.)")
