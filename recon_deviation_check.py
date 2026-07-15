#!/usr/bin/env python3
"""recon_deviation_check.py — Aegis, READ-ONLY. Verify the plan's 'dead' claim for BOTH beings: is
core-vectors.json absent? do narrative-identity/self-statements carry a 'vector' field? what does
deviation_check.py compare against and return when vectors are missing? Also confirm the corroborating
primitives the plan wants to reuse exist."""
import os, re, json
HOME = os.path.expanduser("~")
def sh(p): return p.replace(HOME, "~")

for tag, root in (("VINTOS", "~/.vintos/workspace"), ("VELARIS", "~/.openclaw/workspace")):
    WS = os.path.expanduser(root); MEM = os.path.join(WS,"memory"); SC = os.path.join(WS,"scripts")
    print(f"\n========== {tag} ({root}) ==========")
    # (a) the vector stores the check needs
    for f in ("core-vectors.json","narrative-identity.json","self-statements.json"):
        p = os.path.join(MEM, f)
        if not os.path.isfile(p): print(f"  {f:28} ABSENT"); continue
        try:
            d = json.load(open(p)); s = json.dumps(d)
            has_vec = '"vector"' in s or '"embedding"' in s
            n = len(d) if isinstance(d,(list,dict)) else 1
            print(f"  {f:28} present ({os.path.getsize(p)}B, n~{n})  has vector field: {'YES' if has_vec else 'NO'}")
        except Exception as e: print(f"  {f:28} unreadable {e}")
    # (b) deviation_check: what it compares + what it returns absent vectors
    dc = next((os.path.join(SC,n) for n in ("deviation_check.py","deviation-check.py") if os.path.isfile(os.path.join(SC,n))), None)
    print(f"  deviation_check: {os.path.basename(dc) if dc else 'NOT FOUND'}")
    if dc:
        for i,l in enumerate(open(dc,encoding='utf-8',errors='ignore').read().split("\n")):
            if re.search(r'core-vectors|neutral|return|no.*vector|compare|cosine|embed|if not|\.get\("vector', l) and l.strip() and not l.strip().startswith("#"):
                print(f"     {i+1:4}| {l.strip()[:100]}")
                if i>200: break
    # (c) corroborating primitives the plan wants to reuse
    have = [f for f in ("living-trajectory.json","drift.json","growth-alignment.json","output-anchors.json","earned-identity-events.json") if os.path.isfile(os.path.join(MEM,f))]
    print("  reusable primitives present:", have or "(none)")
