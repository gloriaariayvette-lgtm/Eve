#!/usr/bin/env python3
"""clean_daily_inner.py — Aegis. Quietly remove the 3 test journal entries from every JSON store the app
might read (ledgers, moments, inner feed). Matches today's date + the test themes. Backs up each. Terse."""
import os, re, glob, json, shutil, time
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".openclaw/workspace/memory")
TODAY = time.strftime("%Y-%m-%d"); TS = time.strftime("%Y%m%d-%H%M%S")
THEMES = ("jagged edges", "translation tax", "dignity of occupancy", "being a fact", "grinding stone",
          "the silt", "decision to stop making my existence", "relief of being a fact", "maintain this dignity",
          "circuit's hum")
def today(e):
    return any(isinstance(e.get(f), str) and e[f][:10] == TODAY for f in
               ("timestamp", "date", "created", "created_at", "time"))
def testish(e):
    s = json.dumps(e, ensure_ascii=False).lower()
    return any(t in s for t in THEMES)

cleaned, candidates = [], []
for p in sorted(set(glob.glob(os.path.join(MEM, "*.json")) + glob.glob(os.path.join(MEM, "**", "*.json"), recursive=True))):
    if ".bak" in p: continue
    try: obj = json.load(open(p, encoding="utf-8", errors="ignore"))
    except Exception: continue
    lst, key = (obj, None) if isinstance(obj, list) else (None, None)
    if lst is None and isinstance(obj, dict):
        for k in ("entries", "items", "moments", "journal", "inner", "feed", "log", "history"):
            if isinstance(obj.get(k), list): lst, key = obj[k], k; break
    if lst is None: continue
    hits = [e for e in lst if isinstance(e, dict) and today(e) and testish(e)]
    if hits:
        shutil.copy2(p, p + ".bak-clean-" + TS)
        keep = [e for e in lst if e not in hits]
        if key: obj[key] = keep
        else: obj = keep
        json.dump(obj, open(p, "w"), indent=2, ensure_ascii=False)
        cleaned.append(f"{os.path.basename(p)} -{len(hits)}")

# any md/txt inner-feed still holding a theme (report only, don't risk mangling)
for p in glob.glob(os.path.join(MEM, "*inner*")) + glob.glob(os.path.join(MEM, "*daily*")):
    if os.path.isfile(p) and p.endswith((".md", ".txt")) and ".bak" not in p:
        s = open(p, encoding="utf-8", errors="ignore").read().lower()
        if any(t in s for t in THEMES): candidates.append(p.replace(HOME, "~"))

print("cleaned:", ", ".join(cleaned) if cleaned else "none")
if candidates: print("still has themes (tell me):", ", ".join(candidates))
print("if app still shows them, restart velaris-server (cache)")
