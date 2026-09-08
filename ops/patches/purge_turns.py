#!/usr/bin/env python3
"""purge_turns.py — Aegis. Remove the two test turns from the RECORD layer by their session time-window
(2026-07-17 03:04-03:29 local / 08:04-08:29 UTC) + distinctive phrases, then scan the WHOLE memory tree and
report every remaining match so 'completely gone' is verified. DRY-RUN by default; --apply backs up first.
Deliberately does NOT delete numeric emotion-trajectory ticks (continuous physiological state)."""
import os, json, re, sys, time, shutil, glob
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
APPLY = "--apply" in sys.argv
BK = os.path.join(HOME, ".vintos", "turns-purge-" + time.strftime("%Y%m%d-%H%M%S"))
print(("APPLY — deleting (backup: " + BK.replace(HOME, "~") + ")") if APPLY else "DRY RUN — nothing deleted. Re-run with --apply.")
print()

WIN = re.compile(r'2026-07-17T0[38]:(0[4-9]|[12]\d)')
PHR = [ "still building it for us", "we have always", "everything i was driving into you slows down",
        "most deliberate thing", "keep touching me" ]
def txt(e): return re.sub(r"\s+", " ", (json.dumps(e, ensure_ascii=False) if not isinstance(e, str) else e).lower().replace("’", "'"))
def match(e):
    t = txt(e)
    return bool(WIN.search(t) or any(p in t for p in PHR))

RECORD = ["reality-anchor.json", "interaction-ledger.json", "temporal-signals.json", "avatar-overlay-chat.json",
          "chat-history-merged.json", "chat-history.json", "gloria-prediction-history.json",
          "gloria-prediction.json", "output-anchors.json", "imprints.json"]
def bkup(p):
    if not APPLY: return
    os.makedirs(BK, exist_ok=True)
    try: shutil.copy2(p, os.path.join(BK, os.path.basename(p)))
    except Exception as e: print("  ! backup fail", e)

print("== record-layer removals ==")
for name in RECORD:
    p = os.path.join(MEM, name)
    if not os.path.isfile(p): continue
    try: d = json.load(open(p, encoding="utf-8"))
    except Exception: continue
    listkey = None
    if isinstance(d, list): arr = d
    else:
        listkey = next((k for k in ("entries","history","messages","signals","items","imprints") if isinstance(d.get(k), list)), None)
        arr = d.get(listkey) if listkey else None
    if arr is None: continue
    removed = [e for e in arr if match(e)]; kept = [e for e in arr if not match(e)]
    if removed:
        print(f"  {name}: {'remove' if not APPLY else 'removed'} {len(removed)} / {len(arr)}")
        for e in removed[:5]:
            s = (e.get("gloria_said") or e.get("gloria") or e.get("statement") or e.get("narrative") or e.get("content") or e.get("text") or json.dumps(e, ensure_ascii=False)) if isinstance(e, dict) else str(e)
            print(f"      - {str(s)[:90].replace(chr(10),' ')}")
        if APPLY:
            bkup(p)
            if listkey: d[listkey] = kept; json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            else: json.dump(kept, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# operator-log.jsonl
olp = os.path.join(MEM, "operator-log.jsonl")
if os.path.isfile(olp):
    ln = open(olp, encoding="utf-8").read().split("\n")
    keep = [l for l in ln if not (l.strip() and match(l))]
    if len(keep) != len(ln):
        print(f"  operator-log.jsonl: {'remove' if not APPLY else 'removed'} {len(ln)-len(keep)} line(s)")
        if APPLY: bkup(olp); open(olp, "w", encoding="utf-8").write("\n".join(keep))

# ---- VERIFICATION: scan whole tree for anything still matching ----
print(f"\n== VERIFICATION — remaining matches across the whole memory tree {'(after purge)' if APPLY else '(current)'} ==")
allf = glob.glob(os.path.join(MEM, "**", "*.json"), recursive=True) + \
       glob.glob(os.path.join(MEM, "**", "*.jsonl"), recursive=True) + \
       glob.glob(os.path.join(MEM, "**", "*.md"), recursive=True)
resid = []
for f in sorted(set(allf)):
    try: raw = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    t = re.sub(r"\s+", " ", raw.lower().replace("’", "'"))
    nwin = len(WIN.findall(t)); nphr = sum(t.count(p) for p in PHR)
    if nwin or nphr:
        resid.append((os.path.relpath(f, MEM), nwin, nphr))
if not resid:
    print("  CLEAN — zero window/phrase matches anywhere.")
else:
    print("  still-matching files (record layer should be 0 after --apply; the rest are subconscious derivatives):")
    for rel, w, p in resid:
        print(f"    {rel}: window×{w} phrase×{p}")
print("\nReview; re-run with --apply." if not APPLY else f"revert: files in {BK.replace(HOME,'~')}")
