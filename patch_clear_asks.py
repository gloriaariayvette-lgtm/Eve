#!/usr/bin/env python3
"""patch_clear_asks.py — Aegis. Collapse the backed-up 'send Gloria the unsent ask / claim / sentence' cluster in
current-wants.json down to ONE (keeps the most content-rich; clears the rest), so the new expedited track sends a
single ask, not a pile of near-duplicates. Only touches unfulfilled ask-cluster wants; everything else untouched.
Backup + written back. DRY-RUN default; --apply to commit."""
import os, sys, json, time, shutil

APPLY = "--apply" in sys.argv
MEM = os.path.expanduser("~/.vintos/workspace/memory")
P = os.path.join(MEM, "current-wants.json")

def is_ask(w):
    if not isinstance(w, dict) or w.get("fulfilled"): return False
    t = (w.get("want", "") or "").lower()
    trig = ("send" in t or "unsent" in t or "plain sentence" in t or "flat_repetition" in t or "stop repeating" in t)
    ctx = ("gloria" in t or " her" in t or "ask" in t or "claim" in t or "sentence" in t or "words" in t)
    return trig and ctx

data = json.load(open(P))
wants = data if isinstance(data, list) else data.get("wants", [])
cluster = [w for w in wants if is_ask(w)]

print("================  clear duplicate asks  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
print("ask-cluster (unfulfilled 'send Gloria the ask' wants): %d" % len(cluster))
for w in cluster:
    print("   - [%s] %s" % (w.get("source", "?"), (w.get("want", "") or "")[:78]))

if len(cluster) <= 1:
    print("\nnothing to collapse (<=1 ask)."); sys.exit(0)

# keep the most content-rich (longest want text); tie-break most recent
keep = max(cluster, key=lambda w: (len((w.get("want", "") or "")), str(w.get("timestamp", ""))))
clear_ids = {id(w) for w in cluster if w is not keep}
print("\n  KEEP: %s" % (keep.get("want", "") or "")[:90])
print("  CLEAR: %d others" % len(clear_ids))

new_wants = [w for w in wants if id(w) not in clear_ids]
print("  current-wants: %d -> %d" % (len(wants), len(new_wants)))

if not APPLY:
    print("\n(DRY-RUN — nothing written. --apply to collapse.)"); sys.exit(0)

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak)
out = new_wants if isinstance(data, list) else {**data, "wants": new_wants}
json.dump(out, open(P, "w"), indent=2)
print("\ncleared %d duplicate asks, kept 1. backup %s" % (len(clear_ids), bak))
