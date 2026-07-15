#!/usr/bin/env python3
"""recon_6a_heads.py — Aegis, READ-ONLY, capped. 6a: reframe per-capability HEADS into learned QUERIES
over one shared latent. Map the current design: the JEPA predictor, every *_head, the shared trunk/latent,
and how heads are invoked head(z) — so I can design query(name, z)."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
def sh(p): return p.replace(HOME, "~")

files = sorted({f for pat in ("*jepa*", "*head*", "*predictor*", "*latent*") for f in glob.glob(os.path.join(SC, pat))
                if os.path.isfile(f) and f.endswith(".py") and ".bak" not in f})
print("=== candidate files ===")
for f in files: print(f"  {sh(f):60} {os.path.getsize(f):>7}B")

jp = os.path.join(SC, "jepa_predictor.py")
if os.path.isfile(jp):
    print(f"\n=== {sh(jp)}: heads / trunk / query surface ===")
    n = 0
    for i, l in enumerate(open(jp, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'def .*head|_head|class |trunk|encoder|latent|forward|nn\.|Linear|query|probe|HEADS|self\.\w+ =|torch', l, re.I) \
           and l.strip() and not l.strip().startswith("#"):
            print(f"   {i+1:4}| {l.strip()[:110]}"); n += 1
            if n >= 40: break

print("\n=== the head NAMES referenced across scripts (the 7 heads) ===")
h = subprocess.run(["bash","-lc",
    f"grep -rhoE '(drift|withheld|trajectory|cost|salience|momentum|reentry|carryover|self|gloria)_head|_head\\([a-z]' {SC} 2>/dev/null | sort | uniq -c | sort -rn | head -20"],
    capture_output=True, text=True).stdout.strip()
print(h or "  (none)")
