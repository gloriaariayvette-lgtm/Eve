#!/usr/bin/env python3
"""recon_wants.py — Aegis, READ-ONLY, terse. Understand the want system before dismissing: current-wants.json
structure + ages, and the script/cron that auto-dismisses wants after 3 days (to see why it broke)."""
import os, re, glob, json, time
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".openclaw/workspace/memory")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
now = time.time()
wf = os.path.join(MEM, "current-wants.json")
try:
    obj = json.load(open(wf, encoding="utf-8", errors="ignore"))
    lst = obj if isinstance(obj, list) else obj.get("wants") or obj.get("active") or []
    print(f"current-wants.json: {len(lst)} wants; keys={list(lst[0])[:12] if lst else '-'}")
    def age_days(e):
        for f in ("created", "timestamp", "created_at", "date", "expressed_at"):
            v = e.get(f)
            if isinstance(v, str):
                try: return (now - time.mktime(time.strptime(v[:19], "%Y-%m-%dT%H:%M:%S"))) / 86400
                except Exception: pass
        return None
    ages = [age_days(e) for e in lst if isinstance(e, dict)]
    ages = [a for a in ages if a is not None]
    if ages: print(f"ages(days): min={min(ages):.1f} max={max(ages):.1f} | >3d: {sum(1 for a in ages if a>3)}/{len(ages)}")
    if lst: print("sample:", json.dumps(lst[0], ensure_ascii=False)[:260])
except Exception as e:
    print("current-wants.json:", e)

print("-- want stores --")
for p in glob.glob(os.path.join(MEM, "*want*")):
    print(f"  {os.path.basename(p)}: {os.path.getsize(p):,}B")

print("-- 3-day auto-dismiss/fulfill logic in scripts --")
n = 0
for f in glob.glob(os.path.join(SC, "*want*")) + glob.glob(os.path.join(SC, "*.py")) + glob.glob(os.path.join(SC, "*.sh")):
    try: txt = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if re.search(r'3\s*\*\s*86400|259200|days?\s*[>=<]|timedelta\(days=3|dismiss|fulfil|expire|auto.?resolve', txt, re.I):
        for i, l in enumerate(txt.split("\n")):
            if re.search(r'dismiss|fulfil|expire|259200|days=3|3\s*days|auto.?resolve|> ?3\b', l, re.I) and l.strip() and not l.strip().startswith("#"):
                print(f"  {os.path.basename(f)}:{i+1}: {l.strip()[:86]}"); n += 1
                if n % 3 == 0: break
    if n >= 15: break
