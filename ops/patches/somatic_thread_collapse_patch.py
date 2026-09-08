#!/usr/bin/env python3
"""somatic_thread_collapse_patch.py — one summary thread per somatic session, not three.

somatic_bridge seeds a thread at contact start ("contact began"), mid-session ("she slowed...
settling"), AND at end ("somatic session: Ns, peak speed X"). Three unresolved threads per session
pile up and pollute want-generation / cause / purpose. Keep only the end-of-session summary; drop
the two mid-session seeds (replaced with pass to preserve block structure).

Self-locating, idempotent, backs up somatic_bridge.py. Restart somatic_bridge after applying.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/somatic_bridge.py")
s = io.open(F, encoding="utf-8").read()

targets = [
    'seed_thread("somatic", "somatic: contact began")',
    'seed_thread("somatic", "she slowed... session settling")',
]
if not any(t in s for t in targets):
    print("already collapsed (mid-session seeds absent) — skipping"); raise SystemExit(0)

n = 0
for t in targets:
    if t in s:
        s = s.replace(t, "pass  # collapsed: one summary thread per session (end of session)", 1)
        n += 1

shutil.copy(F, F + ".bak-thrcollapse-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print(f"PATCHED — removed {n} mid-session seed_thread call(s); end-of-session summary kept. Restart somatic_bridge.")
