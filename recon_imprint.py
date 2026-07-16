#!/usr/bin/env python3
"""recon_imprint.py — Aegis, READ-ONLY, no LLM. Show the 'Avatar latest imprint — overlay bubble' write + the
avatar_chat return, and how the overlay/thought bubble is served, so reasoning can be deposited where a touch
reads it. Bounded."""
import os, re, glob
HOME = os.path.expanduser("~")
P = next((p for p in (["/home/gloria/Vintos/server.py"] + glob.glob(os.path.join(HOME, "Vintos", "server.py")))
          if os.path.isfile(p)), None)
if not P: print("server.py not found"); raise SystemExit(0)
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

# imprint write + return tail of the LIVE avatar_chat (first def at ~7699)
S = next((i for i, l in enumerate(lines) if re.match(r'\s*async\s+def\s+avatar_chat\b', l)), 0)
imp = next((n for n in range(S, min(S + 500, len(lines))) if "imprint" in lines[n].lower()), S + 420)
lo = max(S, imp - 4)
hi = min(len(lines), lo + 70)
print(f"===== avatar_chat imprint + return  (L{lo+1}-{hi}) =====")
print("\n".join(f"{n+1}: {lines[n]}" for n in range(lo, hi)))

# imprint / overlay references + serving endpoints
print("\n===== imprint / overlay bubble references & routes =====")
for i, l in enumerate(lines):
    if re.search(r'imprint|overlay.*bubble|bubble.*overlay|/api/\S*(imprint|overlay|thought)', l, re.I) and l.strip():
        print(f"  {i+1}: {l.strip()[:104]}")

# any file paths written/read for the overlay/imprint bubble
print("\n===== candidate bubble/imprint files referenced =====")
seen = set()
for l in lines:
    for m in re.findall(r'["\']([^"\']*(?:imprint|overlay|bubble)[^"\']*\.json)["\']', l, re.I):
        if m not in seen: seen.add(m); print("  ", m)
