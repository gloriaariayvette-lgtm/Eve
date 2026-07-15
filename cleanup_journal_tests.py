#!/usr/bin/env python3
"""cleanup_journal_tests.py — Aegis. Undo the damage from my forced journal test runs today:
(1) RESTORE idle-journal.sh to pristine (from the earliest backup) — this is undoing MY change, done always.
(2) INVENTORY (read-only unless --apply) what the forced runs injected into her real inner life today:
    journal entries, threads, and wants created in the test windows (today, from ~07:40 on).
Nothing in her memory is deleted without --apply, and every edited file is backed up. Shows each item so
Gloria confirms before removal.  Run:  python3 cleanup_journal_tests.py [--apply]"""
import os, re, glob, json, shutil, time, sys
from datetime import datetime
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
MEM = os.path.join(HOME, ".openclaw/workspace/memory")
JP = os.path.join(SC, "idle-journal.sh")
APPLY = "--apply" in sys.argv
TODAY = time.strftime("%Y-%m-%d")
CUTOFF = "07:40"   # my first forced run was 07:43; real prior entry was 03:45
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

# (1) restore idle-journal.sh to pristine (earliest backup = before any reasoning patch)
baks = sorted(glob.glob(JP + ".bak-vjournal-*") + glob.glob(JP + ".bak-vjretry-*") + glob.glob(JP + ".bak-vjmt-*"))
if baks:
    pristine = baks[0]  # earliest
    shutil.copy2(pristine, JP)
    print("RESTORED idle-journal.sh from earliest backup:", sh(pristine))
    cur = open(JP, encoding="utf-8").read()
    print("  reasoning_effort present now?", "yes (NOT clean!)" if "reasoning_effort" in cur else "no — clean",
          "| max_tokens 4000?", "yes (NOT clean!)" if '"max_tokens": 4000' in cur else "no — clean")
else:
    print("!! no backup found to restore idle-journal.sh — tell me")

def after_cutoff(hhmm):
    return hhmm >= CUTOFF

# (2a) journal entries created today after cutoff
jf = os.path.join(MEM, "journal", TODAY + ".md")
print(f"\n=== journal entries in {sh(jf)} (test window: today >= {CUTOFF}) ===")
removed_journal = 0
if os.path.isfile(jf):
    txt = open(jf, encoding="utf-8", errors="ignore").read()
    parts = re.split(r'(?m)(^## \d\d:\d\d)', txt)
    # rebuild: parts = [head, '## HH:MM', body, '## HH:MM', body, ...]
    head = parts[0]; kept = [head]; i = 1
    while i < len(parts):
        hdr = parts[i]; body = parts[i+1] if i+1 < len(parts) else ""
        hhmm = hdr.strip()[3:8]
        is_test = after_cutoff(hhmm)
        tag = "  <== TEST (remove)" if is_test else "  (keep)"
        print(f"  {hdr.strip()}{tag}  | {re.sub(chr(10),' ',body).strip()[:70]}")
        if is_test: removed_journal += 1
        else: kept.append(hdr + body)
        i += 2
    if APPLY and removed_journal:
        shutil.copy2(jf, jf + ".bak-clean-" + TS)
        open(jf, "w", encoding="utf-8").write("".join(kept))
        print(f"  APPLIED: removed {removed_journal} test entr(y/ies). backup saved.")
else:
    print("  (no journal file today)")

# (2b) threads + wants: scan memory json for today's entries in the window
def scan(path):
    try: obj = json.load(open(path, encoding="utf-8", errors="ignore"))
    except Exception: return None, None
    lst = obj if isinstance(obj, list) else None
    key = None
    if lst is None and isinstance(obj, dict):
        for k in ("threads", "wants", "entries", "items", "active"):
            if isinstance(obj.get(k), list): lst, key = obj[k], k; break
    return (obj, lst, key) if lst is not None else (obj, None, None)

def ts_of(e):
    for f in ("timestamp", "date", "created", "created_at", "time"):
        v = e.get(f)
        if isinstance(v, str) and v[:10] == TODAY:
            mt = re.search(r'(\d\d:\d\d)', v)
            return v, (mt.group(1) if mt else "")
    return None, None

def is_test_src(e):
    s = json.dumps(e).lower()
    return any(x in s for x in ("idle-journal", "idle_journal", "journal_bilateral", "latentthread", "latent-thread"))

print(f"\n=== threads / wants injected today >= {CUTOFF} (source: idle-journal/latent) ===")
found_any = False
for path in glob.glob(os.path.join(MEM, "*.json")) + glob.glob(os.path.join(MEM, "**", "*.json"), recursive=True):
    if ".bak" in path: continue
    obj, lst, key = scan(path)
    if not lst: continue
    hits = []
    for e in lst:
        if not isinstance(e, dict): continue
        tv, hh = ts_of(e)
        if tv and hh and after_cutoff(hh) and is_test_src(e):
            hits.append(e)
    if hits:
        found_any = True
        print(f"\n  {sh(path)} — {len(hits)} item(s):")
        for e in hits:
            lbl = e.get("thread") or e.get("want") or e.get("text") or e.get("content") or str({k: e[k] for k in list(e)[:3]})
            print(f"     [{ts_of(e)[0]}] {re.sub(chr(10),' ',str(lbl))[:80]}")
        if APPLY:
            shutil.copy2(path, path + ".bak-clean-" + TS)
            keep = [e for e in lst if e not in hits]
            if key: obj[key] = keep
            else: obj = keep
            json.dump(obj, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            print(f"     APPLIED: removed {len(hits)}. backup saved.")
if not found_any:
    print("  (none matched — threads/wants may store timestamps differently; tell me and I'll widen)")

print("\n" + ("[APPLIED]" if APPLY else "[DRY — nothing in her memory removed. Re-run with --apply to remove the items marked TEST/above.]"))
