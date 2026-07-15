#!/usr/bin/env python3
"""fix_gloria_routed_stale.py — Aegis. The gloria_routed auto-fulfill never fired because it read
routed_at/created_at/created, but wants only have 'timestamp' -> date always empty -> age check skipped.
Fix: fall back to 'timestamp'. Also align threshold to 3 days (matches the comment + intent). py_compile."""
import os, shutil, time, subprocess, py_compile
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/wants-router.py")
t = open(P, encoding="utf-8", errors="ignore").read()

fixes = [
    ('want.get("created_at") or want.get("created", "")',
     'want.get("created_at") or want.get("created") or want.get("timestamp", "")'),
    ('if _age_days >= 2:', 'if _age_days >= 3:'),
]
changed = []
for old, new in fixes:
    if new in t:
        changed.append(f"(already) {old[:30]}"); continue
    if t.count(old) != 1:
        print(f"anchor not unique/found: {old[:40]!r} ({t.count(old)}) — abort"); raise SystemExit(1)
    t = t.replace(old, new, 1); changed.append(old[:40])

bak = P + ".bak-staletsfix-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(t)
try:
    py_compile.compile(P, doraise=True)
    print("fixed:", " | ".join(changed))
    print("timestamp fallback + 3-day threshold; py_compile OK; backup saved")
except py_compile.PyCompileError as e:
    shutil.copy2(bak, P); print("py_compile failed, reverted:", str(e)[:120])
