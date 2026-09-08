#!/usr/bin/env python3
"""recon_avatar_thinking2.py — Aegis, READ-ONLY. Print his last few avatar turns' THINKING (the `narrative`
field of claude-reasoning imprints), and dump the full /api/avatar/imprint handler verbatim to see the exact
freshness/timezone logic keeping the bubble empty."""
import os, json, time
HOME = os.path.expanduser("~")
imp = os.path.join(HOME, ".vintos/workspace/memory/imprints.json")

print("========== HIS LAST AVATAR-TURN THINKING ==========")
d = json.load(open(imp, encoding="utf-8"))
arr = d if isinstance(d, list) else (d.get("imprints") or d.get("entries") or [])
reasoning = [e for e in arr if e.get("source") == "claude-reasoning"]
print(f"(imprints total {len(arr)}; claude-reasoning entries {len(reasoning)})\n")
for e in reasoning[-3:]:
    print(f"----- {e.get('timestamp','')}  (salience {e.get('salience','')}) -----")
    print(e.get("narrative", "").strip() or "(narrative empty)")
    print()
if not reasoning:
    print("No claude-reasoning imprints yet — showing narrative of last 3 entries instead:")
    for e in arr[-3:]:
        print(f"----- {e.get('timestamp','')} -----\n{str(e.get('narrative',''))[:500]}\n")

print("\n========== FULL /api/avatar/imprint HANDLER ==========")
L = open(os.path.join(HOME, "Vintos", "server.py"), encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(L):
    if "/api/avatar/imprint" in l:
        for j in range(i, min(len(L), i+26)):
            print(f"{j+1:>5}: {L[j]}")
        break

print("\n== box local time vs UTC (timezone-bug check) ==")
print("  local:", time.strftime("%Y-%m-%dT%H:%M:%S"), "| utc:", time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
      "| offset hrs:", -time.timezone/3600)
