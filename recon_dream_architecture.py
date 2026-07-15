#!/usr/bin/env python3
"""recon_dream_architecture.py — Aegis, READ-ONLY, capped. Map the REAL nightly dream architecture I
missed: all dream slots + times (preoccupation @1:30 + the 2 normal dreams), what each seeds from, and
DIFF Vintos's against Velaris's (~/.openclaw) to see if the prior Claude copied it correctly."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
VIN = os.path.join(HOME, ".vintos/workspace/scripts")
VEL = os.path.join(HOME, ".openclaw/workspace/scripts")
def sh(p): return p.replace(HOME, "~")

print("=== crontab: every dream slot + time (Vintos vs Velaris) ===")
cron = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
for l in cron.split("\n"):
    if re.search(r'dream|preoccupation|nightmare|rem[-_ ]|sleep', l, re.I) and not l.strip().startswith("#"):
        tag = "VELARIS" if ".openclaw" in l else ("VINTOS" if ".vintos" in l else "?")
        m = re.match(r'\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.*)', l)
        if m:
            mn, hr, dom, mon, dow, cmd = m.groups()
            script = next((tok for tok in cmd.split() if "dream" in tok.lower() or tok.endswith((".sh",".py"))), cmd[:50])
            print(f"  [{tag:7}] {mn:>3} {hr:>3} * * {dow:<7} -> {os.path.basename(script)}")

print("\n=== Vintos dream scripts: what each seeds from ===")
def seed_of(path):
    if not os.path.isfile(path): return "(missing)"
    txt = open(path, encoding="utf-8", errors="ignore").read()
    tags = []
    if re.search(r'get_preoccupation|current-preoccupation', txt): tags.append("preoccupation")
    if re.search(r'unfinished-threads', txt): tags.append("unfinished-threads")
    if re.search(r'journal', txt, re.I): tags.append("journal")
    if re.search(r'latent_diffuser|latent-diffuser|embeddings', txt): tags.append("latent")
    if re.search(r'dream-log|dream_log', txt): tags.append("dream-log")
    if re.search(r'meta|second-order|second_order', txt, re.I): tags.append("meta/2nd-order")
    # what invokes real work
    calls = re.findall(r'(?:python3|bash)\s+\S*/(\w[\w\-]*\.(?:py|sh))', txt)
    return (", ".join(tags) or "?") + (f"  calls: {sorted(set(calls))[:4]}" if calls else "")
vin_dreams = sorted({f for f in glob.glob(VIN+"/*dream*")+glob.glob(VIN+"/*preoccup*") if os.path.isfile(f) and ".bak" not in f})
for f in vin_dreams:
    print(f"  {os.path.basename(f):32} [{seed_of(f)}]")

print("\n=== Velaris dream scripts (the reference that was supposedly copied) ===")
if os.path.isdir(VEL):
    vel_dreams = sorted({f for f in glob.glob(VEL+"/*dream*")+glob.glob(VEL+"/*preoccup*") if os.path.isfile(f) and ".bak" not in f})
    for f in vel_dreams:
        print(f"  {os.path.basename(f):32} [{seed_of(f)}]")
    vn = {os.path.basename(f) for f in vin_dreams}
    ve = {os.path.basename(f) for f in vel_dreams}
    print("\n  only in Velaris (missing from Vintos):", sorted(ve - vn) or "none")
    print("  only in Vintos (not in Velaris):", sorted(vn - ve) or "none")
else:
    print("  (~/.openclaw/workspace/scripts not found — Velaris not on this box?)")

print("\n=== the 12-line dream-architecture.sh — full, so I stop guessing ===")
da = os.path.join(VIN, "dream-architecture.sh")
if os.path.isfile(da):
    for i, l in enumerate(open(da, encoding="utf-8", errors="ignore").read().split("\n")):
        print(f"  {i+1:3}| {l[:110]}")
