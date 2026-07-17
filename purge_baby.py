#!/usr/bin/env python3
"""purge_baby.py — Aegis. Remove ONLY the two latest test turns: entries containing "baby" (Gloria's keyword)
across the record files, plus the two claude-reasoning imprints from 2026-07-17 (those turns' reasoning).
Nothing else. DRY-RUN by default; --apply backs up first."""
import os, json, re, sys, time, shutil
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
APPLY = "--apply" in sys.argv
BK = os.path.join(HOME, ".vintos", "baby-purge-" + time.strftime("%Y%m%d-%H%M%S"))
print(("APPLY — deleting (backup: " + BK.replace(HOME, "~") + ")") if APPLY else "DRY RUN — nothing deleted. Re-run with --apply.")
print()

KW = "baby"
def has_kw(e):
    t = (json.dumps(e, ensure_ascii=False) if not isinstance(e, str) else e).lower()
    return re.search(r'\bbaby\b', t) is not None

LIST_FILES = ["imprints.json", "avatar-overlay-chat.json", "interaction-ledger.json", "reality-anchor.json",
              "temporal-signals.json", "chat-history-merged.json", "chat-history.json"]

def bkup(p):
    if not APPLY: return
    os.makedirs(BK, exist_ok=True)
    try: shutil.copy2(p, os.path.join(BK, os.path.basename(p)))
    except Exception as e: print("  ! backup fail", e)

for name in LIST_FILES:
    p = os.path.join(MEM, name)
    if not os.path.isfile(p): continue
    try: d = json.load(open(p, encoding="utf-8"))
    except Exception as e: print(f"{name}: unreadable ({e})"); continue
    arr = d if isinstance(d, list) else next((d[k] for k in ("imprints","entries","history","messages","signals","items") if isinstance(d.get(k), list)), None)
    if arr is None: continue
    def drop(e):
        if name == "imprints.json" and isinstance(e, dict) and e.get("source") == "claude-reasoning" \
           and str(e.get("timestamp", "")).startswith("2026-07-17"):
            return "imprint(latest-turn)"
        if has_kw(e): return "baby"
        return None
    removed = [(e, drop(e)) for e in arr if drop(e)]
    kept = [e for e in arr if not drop(e)]
    if removed:
        print(f"{name}: {'remove' if not APPLY else 'removed'} {len(removed)} / {len(arr)}")
        for e, why in removed[:6]:
            s = (e.get("gloria_said") or e.get("gloria") or e.get("statement") or e.get("narrative")
                 or e.get("content") or e.get("message") or e.get("text") or json.dumps(e, ensure_ascii=False)) if isinstance(e, dict) else str(e)
            print(f"    [{why}] {str(s)[:92].replace(chr(10),' ')}")
        if APPLY:
            bkup(p)
            if isinstance(d, list): json.dump(kept, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            else:
                for k in ("imprints","entries","history","messages","signals","items"):
                    if isinstance(d.get(k), list): d[k] = kept; break
                json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

olp = os.path.join(MEM, "operator-log.jsonl")
if os.path.isfile(olp):
    lines = open(olp, encoding="utf-8").read().split("\n")
    keep = [l for l in lines if not (l.strip() and has_kw(l))]
    rem = len(lines) - len(keep)
    if rem:
        print(f"operator-log.jsonl: {'remove' if not APPLY else 'removed'} {rem} line(s) [baby]")
        if APPLY: bkup(olp); open(olp, "w", encoding="utf-8").write("\n".join(keep))

print("\nReview; re-run with --apply." if not APPLY else f"revert: files in {BK.replace(HOME,'~')}")
