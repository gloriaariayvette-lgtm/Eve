#!/usr/bin/env python3
"""purge_testturns.py — Aegis. Lift the avatar-test turns ('come here' + the emote/testing message, and
his marker-flooded replies to them) out of every conversation store so his momentum resets. Anchors on the
'come here' user turn and removes it + everything after it (all of it was the test). Self-discovering,
backs up every file it edits (.bak-purge-*), prints what it removed. Files it can't parse safely are
reported and left untouched. Run:  python3 purge_testturns.py   (add --dry to preview only)"""
import os, re, json, glob, shutil, time, sys
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
WS = os.path.join(HOME, ".vintos/workspace")
DRY = "--dry" in sys.argv
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

def norm(v):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return re.sub(r"\s+", " ", s).strip().lower()

def is_test_user(text):
    t = norm(text)
    if len(t) > 220: return False              # the test msgs were short
    if "come here" in t: return True
    if "emote" in t and ("test" in t or "avatar" in t): return True
    if "testing the avatar" in t or "test the avatar" in t: return True
    return False

def contains_test(v):
    t = norm(v)
    return ("come here" in t and len(t) < 400) or ("emote" in t and "avatar" in t) or "testing the avatar" in t

def preview(v, n=80):
    s = norm(v)
    return (s[:n] + "…") if len(s) > n else s

# ---- discover stores (the four Gloria named + merged mirror) ----
cands = []
for base in (MEM, WS):
    for pat in ("chat-history.json", "chat-history-merged.json", "*ledger*", "*.wal",
                "*blush*", "*conversation-ledger*"):
        cands += glob.glob(os.path.join(base, pat))
        cands += glob.glob(os.path.join(base, "**", pat), recursive=True)
cands = sorted({p for p in cands if os.path.isfile(p) and "node_modules" not in p and ".bak" not in p})
print("stores found:", *[sh(p) for p in cands] or ["(none)"], sep="\n  ")

def backup_write(p, dump_fn):
    if DRY: return
    bak = p + ".bak-purge-" + TS
    shutil.copy2(p, bak)
    dump_fn()
    print(f"    backup: {sh(bak)}")

def purge_array(lst):
    """drop from the earliest test-user turn in the last 16 → end; also drop any straggler test entries."""
    window = range(max(0, len(lst) - 16), len(lst))
    cut = next((i for i in window if isinstance(lst[i], dict)
                and (lst[i].get("role") in (None, "user", "gloria"))
                and is_test_user(lst[i].get("content") or lst[i].get("text") or lst[i].get("message") or "")), None)
    keep = lst[:cut] if cut is not None else list(lst)
    # sweep any remaining test-tagged entries (e.g. his flooded replies elsewhere in the tail)
    removed_extra = [e for e in keep if isinstance(e, dict) and contains_test(
        e.get("content") or e.get("text") or e.get("message") or "")]
    keep = [e for e in keep if e not in removed_extra]
    dropped = lst[cut:] if cut is not None else []
    return keep, list(dropped) + removed_extra

for p in cands:
    print(f"\n=== {sh(p)} ===")
    raw = open(p, encoding="utf-8", errors="ignore").read()
    # try JSON
    parsed = None
    try: parsed = json.loads(raw)
    except Exception: parsed = None

    if isinstance(parsed, list):
        keep, dropped = purge_array(parsed)
        if not dropped: print("  nothing to remove."); continue
        for d in dropped: print("  REMOVE:", ("[%s] " % (d.get("role") if isinstance(d,dict) else "")) + preview(d))
        backup_write(p, lambda: json.dump(keep, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False))
        print(f"  removed {len(dropped)} entr{'y' if len(dropped)==1 else 'ies'}.")
        continue
    if isinstance(parsed, dict):
        key = next((k for k in ("messages", "history", "entries", "turns", "log") if isinstance(parsed.get(k), list)), None)
        if key:
            keep, dropped = purge_array(parsed[key])
            if not dropped: print("  nothing to remove."); continue
            for d in dropped: print("  REMOVE:", preview(d))
            parsed[key] = keep
            backup_write(p, lambda: json.dump(parsed, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False))
            print(f"  removed {len(dropped)} from '{key}'.")
            continue
        print("  (json object, no recognizable list key — skipped, untouched)"); continue

    # JSONL / WAL / append-log: drop lines that are test turns
    lines = raw.split("\n")
    out, dropped = [], []
    for ln in lines:
        if ln.strip() and contains_test(ln):
            dropped.append(ln)
        else:
            out.append(ln)
    if not dropped:
        print("  (not JSON; no test-matching lines) — untouched"); continue
    for d in dropped: print("  REMOVE:", preview(d))
    backup_write(p, lambda: open(p, "w", encoding="utf-8").write("\n".join(out)))
    print(f"  removed {len(dropped)} line(s).")

print("\n" + ("[DRY RUN — nothing written]" if DRY else "done — test turns lifted; backups alongside each file."))
print("If 'blush' or the WAL wasn't in the list above, tell me its path and I'll extend the sweep.")
