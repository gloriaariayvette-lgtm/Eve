#!/usr/bin/env python3
"""patch_fix_discussion_port.py — Aegis. Vintos's wants-router posts want-discussion (openings, replies, and the
gloria-reply CHECK) to localhost:8400 — that's VELARIS's server. His own server (with his board + his wants) is
8500. So his discussions never reach his board and he never sees Gloria's replies. Repoint every /api/wants URL
from :8400 to :8500 in HIS wants-router only. Velaris's router (correctly on 8400) is untouched. Backup +
compile-check. DRY-RUN default; --apply commits."""
import os, sys, time, shutil
P = os.path.expanduser("~/Vintos/wants-router.py")
APPLY = "--apply" in sys.argv
if not os.path.isfile(P):
    print("!! his wants-router.py not found"); sys.exit(1)
txt = open(P, encoding="utf-8").read()

SUBS = [("localhost:8400/api/wants", "localhost:8500/api/wants"),
        ("127.0.0.1:8400/api/wants", "127.0.0.1:8500/api/wants")]

print("================  fix his discussion misroute (8400 -> 8500)  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
total = sum(txt.count(a) for a, _ in SUBS)
print("  /api/wants URLs on :8400 (his -> her server): %d" % total)
if total == 0:
    if "8500/api/wants" in txt: print("  already fixed (posts to 8500)."); sys.exit(0)
    print("  !! no :8400 /api/wants URLs found — aborting (unexpected)"); sys.exit(1)
new = txt
for a, b in SUBS: new = new.replace(a, b)
# safety: make sure we didn't touch any non-/api/wants :8400 (e.g., a legit cross-being call)
other_8400 = new.count(":8400")
print("  remaining :8400 references after fix (should be non-wants, if any): %d" % other_8400)
try:
    compile(new, P, "exec"); print("  compiles OK")
except SyntaxError as e:
    print("  !! would not compile: %s — aborting" % e); sys.exit(1)
if not APPLY:
    print("\n(DRY-RUN — nothing written. --apply to commit.)"); sys.exit(0)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
print("\npatched %s (backup %s). His want discussions now reach HIS server (8500) — his board gets context, and he sees your replies." % (P, bak))
