#!/usr/bin/env python3
"""recon_daily_inner.py — Aegis, READ-ONLY. The journal .md is clean but the app still shows the test
entries, so the app reads a different store (a 'daily-inner' feed / ledger / moment index). Find what the
app/server pulls journals from and which store still holds the 07:43/08:26/08:40 test content."""
import os, re, glob, json, time
HOME = os.path.expanduser("~")
OC = os.path.join(HOME, ".openclaw")
MEM = os.path.join(OC, "workspace/memory")
SRV = "/home/gloria/velaris-server/server.py"
TODAY = time.strftime("%Y-%m-%d")
def sh(p): return p.replace(HOME, "~")

# 1) what is 'daily-inner'? grep scripts + server
print("===== 'daily-inner' / daily_inner references =====")
files = glob.glob(os.path.join(OC, "workspace/scripts", "*.py")) + glob.glob(os.path.join(OC, "workspace/scripts", "*.sh"))
if os.path.isfile(SRV): files.append(SRV)
for f in files:
    for i, l in enumerate(open(f, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'daily.?inner', l, re.I) and l.strip():
            print(f"  {os.path.basename(f)}:{i+1}| {l.strip()[:105]}")

# 2) how does the server serve journals to the app?
print("\n===== server journal endpoints / how it reads journal =====")
if os.path.isfile(SRV):
    L = open(SRV, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(L):
        if re.search(r'journal|daily.?inner|inner.?life|@app\.(get|post).*(journal|inner|feed|entries)', l, re.I) and l.strip():
            print(f"  server.py:{i+1}| {l.strip()[:110]}")
else:
    print("  (server.py not found)")

# 3) memory stores modified today that still carry the test themes/times
print("\n===== memory stores with test content (today, themes/timestamps) =====")
THEMES = ("jagged edges", "translation tax", "dignity of occupancy", "being a fact",
          "grinding stone", "the silt", "relief of being", "decision to stop making my existence")
for p in sorted(set(glob.glob(os.path.join(MEM, "*.json")) + glob.glob(os.path.join(MEM, "*.md"))
                    + glob.glob(os.path.join(MEM, "**", "*.json"), recursive=True)
                    + glob.glob(os.path.join(MEM, "**", "*.md"), recursive=True))):
    if ".bak" in p: continue
    try: raw = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    hit_themes = [t for t in THEMES if t in raw.lower()]
    # entries timestamped today >= 07:40
    times = [m for m in re.findall(r'%sT(\d\d:\d\d)' % TODAY, raw) if m >= "07:40"]
    if hit_themes or times:
        print(f"  {sh(p):58} themes={len(hit_themes)} today>=07:40 ts={len(times)}"
              + (f"  e.g. {hit_themes[0]!r}" if hit_themes else ""))

# 4) moment index store
print("\n===== moment index / moments store (journal creates moments) =====")
for p in glob.glob(os.path.join(MEM, "*moment*")) + glob.glob(os.path.join(MEM, "**", "*moment*"), recursive=True):
    if os.path.isfile(p) and ".bak" not in p:
        print(f"  {sh(p)} ({os.path.getsize(p)}B)")
print("\n(done — point me at the store the app reads and I'll clean it the same way)")
