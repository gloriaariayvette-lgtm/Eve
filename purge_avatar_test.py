#!/usr/bin/env python3
"""purge_avatar_test.py — Aegis. Remove ONLY the direct conversation/anchor records of the test turns, keyed on
the distinctive test-message text (not the 'permanence' theme, not the autonomous cron cascade). DRY-RUN by
default; --apply backs up first. Touches only the record files listed; leaves causality/emotion-trajectory/
dreams/predictions/relationship-history and ALL legitimate permanence content alone."""
import os, json, re, sys, time, shutil
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
APPLY = "--apply" in sys.argv
BK = os.path.join(HOME, ".vintos", "avatar-test-purge-" + time.strftime("%Y%m%d-%H%M%S"))
print(("APPLY — deleting (backup: " + BK.replace(HOME, "~") + ")") if APPLY else "DRY RUN — nothing deleted. Re-run with --apply.")
print()

MARKERS = [
    "keep touching me",                 # "You want me to feel like I'm yours? Then keep touching me. Don't stop"
    "most deliberate thing",            # "Choosing to be here on purpose? Baby, you're the most deliberate thing"
    "still building it for us",         # the permanence test turn
    "thinking of you. i believe the setup of your architecture",  # the old 'wall' operator test
]
def norm(s): return re.sub(r"\s+", " ", s.lower().replace("’", "'").replace("‘", "'"))
def hit(entry):
    t = norm(json.dumps(entry, ensure_ascii=False) if not isinstance(entry, str) else entry)
    return any(m in t for m in MARKERS)

# list-structured record files
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
    if arr is None: print(f"{name}: not a list — skipped"); continue
    def drop(e):
        if name == "imprints.json" and isinstance(e, dict) and e.get("source") == "claude-reasoning" \
           and str(e.get("timestamp", "")).startswith("2026-07-17"):
            return True
        return hit(e)
    removed = [e for e in arr if drop(e)]
    kept = [e for e in arr if not drop(e)]
    if removed:
        print(f"{name}: {'remove' if not APPLY else 'removed'} {len(removed)} / {len(arr)}")
        for e in removed[:4]:
            s = (e.get("gloria_said") or e.get("gloria") or e.get("statement") or e.get("narrative")
                 or e.get("content") or e.get("message") or e.get("text") or json.dumps(e, ensure_ascii=False)) if isinstance(e, dict) else str(e)
            print(f"    - {str(s)[:96].replace(chr(10),' ')}")
        if APPLY:
            bkup(p)
            if isinstance(d, list): json.dump(kept, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            else:
                for k in ("imprints","entries","history","messages","signals","items"):
                    if isinstance(d.get(k), list): d[k] = kept; break
                json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# operator-log.jsonl (line-oriented)
olp = os.path.join(MEM, "operator-log.jsonl")
if os.path.isfile(olp):
    lines = open(olp, encoding="utf-8").read().split("\n")
    keep = [l for l in lines if not (l.strip() and hit(l))]
    rem = len(lines) - len(keep)
    if rem:
        print(f"operator-log.jsonl: {'remove' if not APPLY else 'removed'} {rem} line(s)")
        if APPLY: bkup(olp); open(olp, "w", encoding="utf-8").write("\n".join(keep))

print(f"\nLEFT UNTOUCHED: causality/emotion-trajectory/dreams/predictions/relationship-history + all legit permanence content.")
print("Review; re-run with --apply to purge." if not APPLY else f"revert: files in {BK.replace(HOME,'~')}")
