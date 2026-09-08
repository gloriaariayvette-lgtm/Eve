#!/usr/bin/env python3
"""erase_test_pollution.py — Aegis. Erase today's test pollution from Vintos's memory. Backs up every file it
touches to ~/.vintos/test-erase-backup-<ts>/ FIRST, then removes only entries timestamped >= 2026-07-16 05:00
(incl. my claude-reasoning imprint deposits), deletes the diagnostics + today's chat-drafts, and reports
exactly what was removed. LEAVES avatar-overlay-chat.json and all derived state untouched. Fully reversible."""
import os, json, glob, shutil, time
from datetime import datetime
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
CUTOFF = datetime(2026, 7, 16, 5, 0)
BK = os.path.join(HOME, ".vintos", "test-erase-backup-" + time.strftime("%Y%m%d-%H%M%S"))
os.makedirs(BK, exist_ok=True)

def parse_ts(e):
    for k in ("timestamp", "ts", "time", "created_at"):
        v = e.get(k) if isinstance(e, dict) else None
        if v:
            try:
                d = datetime.fromisoformat(str(v).replace("Z", ""))
                return d.replace(tzinfo=None)
            except Exception: pass
    return None

def backup(p):
    try: shutil.copy2(p, os.path.join(BK, os.path.basename(p))); return True
    except Exception as e: print("  ! backup failed", p, e); return False

# --- timestamped list files: drop entries >= CUTOFF (keep no-ts + older) ---
LIST_FILES = ["imprints.json", "chat-history-merged.json", "chat-history.json",
              "relationship-history.json", "gloria-prediction-history.json"]
print(f"backup dir: {BK.replace(HOME,'~')}\ncutoff: {CUTOFF} (remove entries at/after this)\n")
for name in LIST_FILES:
    p = os.path.join(MEM, name)
    if not os.path.isfile(p): continue
    try: d = json.load(open(p, encoding="utf-8"))
    except Exception as e: print(f"{name}: can't read ({e}) — skipped"); continue
    if not isinstance(d, list):
        print(f"{name}: not a top-level list — LEFT UNTOUCHED (tell me if it needs cleaning)"); continue
    kept, removed = [], []
    for e in d:
        ts = parse_ts(e)
        (removed if (ts and ts >= CUTOFF) else kept).append(e)
    if not removed:
        print(f"{name}: nothing >= cutoff (0 removed, {len(kept)} kept)"); continue
    backup(p)
    json.dump(kept, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{name}: removed {len(removed)}, kept {len(kept)}")
    for e in removed[:8]:
        c = (e.get("content") or e.get("message") or e.get("narrative") or e.get("text") or "") if isinstance(e, dict) else str(e)
        print(f"    - {str(parse_ts(e)):19} {str(e.get('source','') if isinstance(e,dict) else '')[:16]:16} {str(c)[:80].replace(chr(10),' ')}")

# --- loose test files: back up then delete ---
print("\nloose files:")
loose = ["/tmp/vintos-chat-trace.json", "/tmp/vintos-full-prompt.txt"]
loose += glob.glob(os.path.join(MEM, "chat-drafts", "2026-07-16_*.md"))
for p in loose:
    if os.path.isfile(p):
        backup(p)
        try: os.remove(p); print(f"  deleted {p.replace(HOME,'~')}")
        except Exception as e: print(f"  ! couldn't delete {p}: {e}")

print("\nLEFT UNTOUCHED (by your call): avatar-overlay-chat.json, emotional-snapshots/, and all derived state")
print(f"revert everything: cp {BK.replace(HOME,'~')}/* to their original locations")
print("done.")
