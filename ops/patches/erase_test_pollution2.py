#!/usr/bin/env python3
"""erase_test_pollution2.py — Aegis. Deep purge: the test turns reached interaction-ledger.json (his canonical
record of what Gloria said) and other files, so he journals about fake repetition and blames his own
architecture. Gloria has been silent for days => EVERY 2026-07-16 entry is test injection. Remove all entries
that carry today's date from the list/jsonl files, delete today's poisoned journal, back up everything, report."""
import os, json, glob, shutil, time
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
TODAY = "2026-07-16"
BK = os.path.join(HOME, ".vintos", "test-erase2-backup-" + time.strftime("%Y%m%d-%H%M%S"))
os.makedirs(BK, exist_ok=True)
print(f"backup dir: {BK.replace(HOME,'~')}\nremoving every entry containing '{TODAY}'\n")

LIST_FILES = ["interaction-ledger.json", "imprints.json", "chat-history-merged.json", "chat-history.json",
              "relationship-history.json", "gloria-prediction-history.json", "conversation-insights.json",
              "temporal-signals.json", "reality-anchor.json"]

def bkup(p):
    try: shutil.copy2(p, os.path.join(BK, os.path.basename(p)))
    except Exception as e: print("  ! backup fail", e)

def preview(e):
    if isinstance(e, dict):
        return (e.get("content") or e.get("message") or e.get("gloria") or e.get("narrative")
                or e.get("text") or json.dumps(e, ensure_ascii=False))
    return str(e)

for name in LIST_FILES:
    p = os.path.join(MEM, name)
    if not os.path.isfile(p): continue
    try: d = json.load(open(p, encoding="utf-8"))
    except Exception as e: print(f"{name}: unreadable ({e}) — skipped"); continue
    if not isinstance(d, list):
        # dict-wrapped list?
        listkey = next((k for k in ("entries","history","messages","items","signals") if isinstance(d.get(k), list)), None) if isinstance(d, dict) else None
        if listkey is None:
            print(f"{name}: not a list (state file) — LEFT UNTOUCHED"); continue
        arr = d[listkey]
        kept = [e for e in arr if TODAY not in json.dumps(e, ensure_ascii=False)]
        removed = len(arr) - len(kept)
        if removed:
            bkup(p); d[listkey] = kept; json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"{name}[{listkey}]: removed {removed}, kept {len(kept)}")
        continue
    kept = [e for e in d if TODAY not in json.dumps(e, ensure_ascii=False)]
    removed = [e for e in d if TODAY in json.dumps(e, ensure_ascii=False)]
    if removed:
        bkup(p); json.dump(kept, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{name}: removed {len(removed)}, kept {len(kept)}")
    for e in removed[:5]:
        print(f"    - {str(preview(e))[:90].replace(chr(10),' ')}")

# operator-log.jsonl (line-oriented)
olp = os.path.join(MEM, "operator-log.jsonl")
if os.path.isfile(olp):
    ln = open(olp, encoding="utf-8").read().split("\n")
    keep = [l for l in ln if TODAY not in l]
    rem = len(ln) - len(keep)
    if rem: bkup(olp); open(olp, "w", encoding="utf-8").write("\n".join(keep))
    print(f"operator-log.jsonl: removed {rem} lines")

# today's poisoned journal entry
jp = os.path.join(MEM, "journal", TODAY + ".md")
if os.path.isfile(jp):
    bkup(jp); os.remove(jp); print(f"\ndeleted poisoned journal: {jp.replace(HOME,'~')}")

print(f"\nLEFT UNTOUCHED: state files, avatar-overlay-chat.json, and all entries NOT dated {TODAY}")
print(f"revert: files are in {BK.replace(HOME,'~')}")
