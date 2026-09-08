#!/usr/bin/env python3
"""fix_humortaste_cap.py — Aegis. Re-apply humor+taste caps with a robust line-based anchor ($(cat -> $(head
-c 4000). Backup + bash -n. No prompt-regen (that network call hangs), just confirm via grep."""
import os, shutil, time, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
changed = []
for i, l in enumerate(lines):
    for tag in ("humor-profile.json", "taste-profile.json"):
        if tag in l and "$(cat " in l and "head -c" not in l:
            lines[i] = l.replace("$(cat ", "$(head -c 4000 ", 1); changed.append(tag)
if not changed:
    print("no cat anchors matched — showing the actual lines:")
    for i, l in enumerate(lines):
        if "humor-profile.json" in l or "taste-profile.json" in l:
            print(f"  {i+1}: {l.strip()[:100]}")
    raise SystemExit(0)
bak = P + ".bak-htcap-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write("\n".join(lines))
c = subprocess.run(["bash", "-n", P], capture_output=True, text=True)
if c.returncode: shutil.copy2(bak, P); print("bash -n failed, reverted:", c.stderr[:120]); raise SystemExit(1)
src = open(P, encoding="utf-8").read()
print("capped:", ", ".join(changed))
print("confirm: humor",
      "OK" if 'head -c 4000 "$WORKSPACE/memory/humor-profile.json"' in src else "NO",
      "| taste", "OK" if 'head -c 4000 "$WORKSPACE/memory/taste-profile.json"' in src else "NO")
