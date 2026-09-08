#!/usr/bin/env python3
"""purge_two_turns.py — Aegis. Remove ONLY the two turns whose reasoning was already deleted: 03:06 and 03:17-18
on 2026-07-17 (local) / 08:06, 08:17-18 (UTC). Matches those exact timestamp minutes, case-sensitive. No phrases,
no other turns, no 07-15 content. DRY-RUN by default; --apply backs up first."""
import os, json, sys, time, shutil
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
APPLY = "--apply" in sys.argv
BK = os.path.join(HOME, ".vintos", "two-turns-purge-" + time.strftime("%Y%m%d-%H%M%S"))
print(("APPLY — deleting (backup: " + BK.replace(HOME, "~") + ")") if APPLY else "DRY RUN — nothing deleted. Re-run with --apply.\n")

TS = ["2026-07-17T03:06", "2026-07-17T03:17", "2026-07-17T03:18",
      "2026-07-17T08:06", "2026-07-17T08:17", "2026-07-17T08:18"]
def match(e):
    s = json.dumps(e, ensure_ascii=False) if not isinstance(e, str) else e
    return any(t in s for t in TS)

RECORD = ["reality-anchor.json", "interaction-ledger.json", "temporal-signals.json", "avatar-overlay-chat.json",
          "chat-history-merged.json", "chat-history.json", "gloria-prediction-history.json",
          "gloria-prediction.json", "output-anchors.json", "imprints.json"]
def bkup(p):
    if not APPLY: return
    os.makedirs(BK, exist_ok=True)
    try: shutil.copy2(p, os.path.join(BK, os.path.basename(p)))
    except Exception as e: print("  ! backup fail", e)

for name in RECORD:
    p = os.path.join(MEM, name)
    if not os.path.isfile(p): continue
    try: d = json.load(open(p, encoding="utf-8"))
    except Exception: continue
    lk = None
    if isinstance(d, list): arr = d
    else:
        lk = next((k for k in ("entries","history","messages","signals","items","imprints") if isinstance(d.get(k), list)), None)
        arr = d.get(lk) if lk else None
    if arr is None: continue
    rem = [e for e in arr if match(e)]; kept = [e for e in arr if not match(e)]
    if rem:
        print(f"{name}: {'remove' if not APPLY else 'removed'} {len(rem)} / {len(arr)}")
        for e in rem:
            s = (e.get("gloria_said") or e.get("gloria") or e.get("statement") or e.get("narrative") or e.get("content") or e.get("text") or json.dumps(e, ensure_ascii=False)) if isinstance(e, dict) else str(e)
            print(f"    - {str(s)[:88].replace(chr(10),' ')}")
        if APPLY:
            bkup(p)
            if lk: d[lk] = kept; json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            else: json.dump(kept, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("\nReview; if it's the two turns, re-run with --apply." if not APPLY else f"\nDone. revert: files in {BK.replace(HOME,'~')}")
