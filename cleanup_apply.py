#!/usr/bin/env python3
"""cleanup_apply.py — Aegis. FOR REAL (not dry): (1) restore idle-journal.sh from TODAY's pre-reasoning
snapshot (.bak-vjournal-2026071*, NOT the stale June backup). (2) remove my forced-test journal entries
(today >= 07:40), and the threads + wants those runs seeded. Every edited file backed up first."""
import os, re, glob, json, shutil, time
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
MEM = os.path.join(HOME, ".openclaw/workspace/memory")
JP = os.path.join(SC, "idle-journal.sh")
TODAY = time.strftime("%Y-%m-%d")
CUTOFF = "07:40"
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

# (1) restore from TODAY's pre-reasoning snapshot specifically
today_cln = sorted(b for b in glob.glob(JP + ".bak-vjournal-2026071*")
                   if "reasoning_effort" not in open(b, encoding="utf-8", errors="ignore").read())
if today_cln:
    src = today_cln[0]
    shutil.copy2(src, JP)
    cur = open(JP, encoding="utf-8").read()
    print("RESTORED idle-journal.sh from TODAY's snapshot:", sh(src))
    print("  clean?", "YES" if "reasoning_effort" not in cur and '"max_tokens": 4000' not in cur else "NO",
          "| size", len(cur), "chars")
else:
    print("!! today's .bak-vjournal snapshot not found — NOT restoring (tell me)")

# (2a) remove test journal entries (today >= CUTOFF)
jf = os.path.join(MEM, "journal", TODAY + ".md")
print(f"\n=== journal {sh(jf)} ===")
if os.path.isfile(jf):
    txt = open(jf, encoding="utf-8", errors="ignore").read()
    parts = re.split(r'(?m)(^## \d\d:\d\d)', txt)
    kept = [parts[0]]; removed = []
    i = 1
    while i < len(parts):
        hdr = parts[i]; body = parts[i+1] if i+1 < len(parts) else ""
        hhmm = hdr.strip()[3:8]
        if hhmm >= CUTOFF:
            removed.append(hdr.strip())
        else:
            kept.append(hdr + body)
        i += 2
    if removed:
        shutil.copy2(jf, jf + ".bak-clean-" + TS)
        open(jf, "w", encoding="utf-8").write("".join(kept))
        print("  REMOVED entries:", ", ".join(removed))
        print("  kept everything before", CUTOFF, "(incl. the real 03:45). backup saved.")
    else:
        print("  no test entries found")
else:
    print("  (no journal today)")

# (2b) remove seeded threads + wants (today >= CUTOFF, source idle-journal/latent)
def process(path):
    try: obj = json.load(open(path, encoding="utf-8", errors="ignore"))
    except Exception: return
    lst, key = (obj, None) if isinstance(obj, list) else (None, None)
    if lst is None and isinstance(obj, dict):
        for k in ("threads", "wants", "entries", "items", "active"):
            if isinstance(obj.get(k), list): lst, key = obj[k], k; break
    if lst is None: return
    def is_test(e):
        if not isinstance(e, dict): return False
        s = json.dumps(e).lower()
        if not any(x in s for x in ("idle-journal", "idle_journal", "journal_bilateral", "latentthread", "latent-thread")):
            return False
        for f in ("timestamp", "date", "created", "created_at", "time"):
            v = e.get(f)
            if isinstance(v, str) and v[:10] == TODAY:
                mt = re.search(r'(\d\d:\d\d)', v)
                if mt and mt.group(1) >= CUTOFF: return True
        return False
    hits = [e for e in lst if is_test(e)]
    if not hits: return
    shutil.copy2(path, path + ".bak-clean-" + TS)
    keep = [e for e in lst if e not in hits]
    if key: obj[key] = keep
    else: obj = keep
    json.dump(obj, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\n  {sh(path)}: removed {len(hits)} (backup saved)")
    for e in hits:
        lbl = e.get("thread") or e.get("want") or e.get("text") or e.get("content") or ""
        print("     -", re.sub(r"\s+", " ", str(lbl))[:78])

print("\n=== threads / wants ===")
seen = set()
for path in glob.glob(os.path.join(MEM, "*.json")) + glob.glob(os.path.join(MEM, "**", "*.json"), recursive=True):
    rp = os.path.realpath(path)
    if rp in seen or ".bak" in path: continue
    seen.add(rp); process(path)

print("\n[DONE] her inner life restored to before my tests; idle-journal.sh back to today's real version.")
