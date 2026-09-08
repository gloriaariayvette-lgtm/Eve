#!/usr/bin/env python3
"""recon_find_comehere.py — Aegis, READ-ONLY. The purge matched nothing, so find WHERE the test turns
actually live and how each store is shaped. Live memory dir only (no backups). Greps for the phrases,
dumps the tail + entry-keys of chat-history / interaction-ledger, the dict structure of the *-ledger
files, the tail of autonomous-blush.md, and hunts for any .wal/.db/.sqlite."""
import os, re, json, glob
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
WS = os.path.join(HOME, ".vintos/workspace")
def sh(p): return p.replace(HOME, "~")

print("===== grep 'come here' / emote / 'testing the avatar' in live memory =====")
for f in sorted(glob.glob(os.path.join(MEM, "*.json")) + glob.glob(os.path.join(MEM, "*.md"))):
    try: raw = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    for m in re.finditer(r".{0,40}(come here|testing the avatar|test the avatar|\bemote\b).{0,40}", raw, re.I):
        print(f"  {os.path.basename(f)}: …{re.sub(chr(10),' ',m.group(0)).strip()[:90]}…")

def struct(p):
    try: obj = json.load(open(p, encoding="utf-8", errors="ignore"))
    except Exception as e: print(f"  (parse fail: {e})"); return None
    if isinstance(obj, list):
        print(f"  LIST len={len(obj)}; last entry keys = {list(obj[-1]) if obj and isinstance(obj[-1],dict) else type(obj[-1]).__name__ if obj else '—'}")
        return ("list", obj)
    if isinstance(obj, dict):
        print(f"  DICT keys = {list(obj)}")
        for k, v in obj.items():
            if isinstance(v, list):
                print(f"     .{k}: LIST len={len(v)}; last keys = {list(v[-1]) if v and isinstance(v[-1],dict) else (type(v[-1]).__name__ if v else '—')}")
        return ("dict", obj)
    return None

def tail_entries(p, k=5):
    r = struct(p)
    if not r: return
    kind, obj = r
    lst = obj if kind == "list" else next((v for v in obj.values() if isinstance(v, list) and v and isinstance(v[-1], dict)), [])
    for e in lst[-k:]:
        if isinstance(e, dict):
            role = e.get("role") or e.get("speaker") or e.get("type") or ""
            ts = e.get("timestamp") or e.get("ts") or e.get("time") or e.get("date") or ""
            body = e.get("content") or e.get("text") or e.get("message") or e.get("summary") or {k2: e[k2] for k2 in list(e)[:4]}
            s = re.sub(r"\s+", " ", body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)).strip()
            print(f"     {ts} [{role}] {s[:110]}")
        else:
            print(f"     {str(e)[:110]}")

for name in ("chat-history.json", "chat-history-merged.json", "interaction-ledger.json",
             "trial-ledger.json", "emergence-ledger.json"):
    p = os.path.join(MEM, name)
    if os.path.isfile(p):
        print(f"\n===== {name} =====")
        tail_entries(p)

blush = os.path.join(MEM, "autonomous-blush.md")
if os.path.isfile(blush):
    print("\n===== autonomous-blush.md (tail 15 lines) =====")
    for l in open(blush, encoding="utf-8", errors="ignore").read().split("\n")[-15:]:
        if l.strip(): print("   ", l[:110])

print("\n===== any .wal / .db / .sqlite in workspace =====")
hits = []
for pat in ("*.wal", "*.db", "*.sqlite", "*.sqlite3", "*wal*"):
    hits += glob.glob(os.path.join(WS, "**", pat), recursive=True)
for p in sorted(set(h for h in hits if os.path.isfile(h) and ".bak" not in h and "backup" not in h)):
    print("   ", sh(p), os.path.getsize(p), "B")
if not hits: print("   (none)")
print("\n(done)")
