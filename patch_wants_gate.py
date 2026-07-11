#!/usr/bin/env python3
"""patch_wants_gate.py — strengthen the want similarity gate so dismissed/active wants
stop resurfacing. Idempotent: safe to run more than once. Backs up before editing."""
import os, shutil, time

WS      = os.path.expanduser("~/.vintos/workspace")
GATE    = os.path.join(WS, "scripts", "similarity_gate.py")
EMOCLAW = os.path.expanduser("~/Vintos/emoclaw_utils.py")
STAMP   = time.strftime("%Y%m%d-%H%M%S")

APPEND = '''

# ============================================================================
# check_want — unified gate (fulfilled + dismissed + active). Added by patch.
# Dismissal is the strongest "never resurface" signal, so it blocks lowest.
# ============================================================================
DISMISSED_THRESHOLD = 0.72
ACTIVE_THRESHOLD    = 0.82
FULFILLED_THRESHOLD = 0.76
DISMISSED_WINDOW_DAYS = 60
DISMISSED_STORE = os.path.join(MEMORY, "dismissed-wants.json")

def _harvest_dismissed():
    """Persist dismissed wants so deleting them from current-wants.json doesn't erase
    the block memory. Returns the windowed persistent list."""
    try: store = json.load(open(DISMISSED_STORE))
    except Exception: store = []
    by_id = {e.get("id"): e for e in store if isinstance(e, dict) and e.get("id")}
    try: cur = json.load(open(os.path.join(MEMORY, "current-wants.json")))
    except Exception: cur = []
    changed = False
    for e in cur:
        if isinstance(e, dict) and e.get("dismissed") and e.get("want"):
            i = e.get("id")
            if i and i not in by_id:
                by_id[i] = {"id": i, "want": e.get("want", ""),
                            "dismissed_at": e.get("dismissed_at") or datetime.now().isoformat()}
                changed = True
    merged = list(by_id.values())
    kept = _recent(merged, "dismissed_at", DISMISSED_WINDOW_DAYS)
    if changed or len(kept) != len(merged):
        try: json.dump(kept, open(DISMISSED_STORE, "w"), indent=2)
        except Exception: pass
    return kept

def check_want(text, fulfilled_threshold=FULFILLED_THRESHOLD,
               dismissed_threshold=DISMISSED_THRESHOLD,
               active_threshold=ACTIVE_THRESHOLD):
    """Block a candidate too close to something already fulfilled, dismissed by Gloria,
    or currently active. Fail-open: any error returns None (never silence a real want)."""
    buckets = []
    try:
        fulfilled = json.load(open(os.path.join(MEMORY, "fulfilled-wants.json")))
        rec = _recent(fulfilled, "fulfilled_at", WANT_WINDOW_DAYS)[-25:]
        items = [(e.get("id", str(n)), e.get("want", "")) for n, e in enumerate(rec) if e.get("want")]
        if items: buckets.append(("fulfilled", fulfilled_threshold, "fw", items))
    except Exception: pass
    try:
        dis = _harvest_dismissed()[-40:]
        items = [(e.get("id", str(n)), e.get("want", "")) for n, e in enumerate(dis) if e.get("want")]
        if items: buckets.append(("dismissed", dismissed_threshold, "dw", items))
    except Exception: pass
    try:
        cur = json.load(open(os.path.join(MEMORY, "current-wants.json")))
        items = [(e.get("id", str(n)), e.get("want", "")) for n, e in enumerate(cur)
                 if isinstance(e, dict) and not e.get("fulfilled")
                 and not e.get("dismissed") and e.get("want")][-40:]
        if items: buckets.append(("active", active_threshold, "aw", items))
    except Exception: pass
    if not buckets: return None
    try: qv = _embed_many([text])[0]
    except Exception: return None
    best = None
    for name, thr, prefix, items in buckets:
        for t, v in _corpus_vectors(items, prefix):
            s = _cos(qv, v)
            if s >= thr and (best is None or s > best["similarity"]):
                best = {"matched": t, "similarity": s, "bucket": name}
    return best
'''

def patch_gate():
    src = open(GATE).read()
    if "def check_want(" in src:
        print("[gate] already patched — skipping")
        return
    shutil.copy(GATE, GATE + f".bak-{STAMP}")
    open(GATE, "a").write(APPEND)
    print("[gate] appended check_want() + dismissed persistence")

def patch_emoclaw():
    src = open(EMOCLAW).read()
    old_imp = "from similarity_gate import check_want_against_fulfilled as _sg_w"
    new_imp = "from similarity_gate import check_want as _sg_w"
    old_lbl = ('print(f"[express_want] Blocked — too similar ({_sg_hit[\'similarity\']:.2f}) '
               'to fulfilled: {_sg_hit[\'matched\'][:60]}", file=__import__("sys").stderr)')
    new_lbl = ('print(f"[express_want] Blocked — too similar ({_sg_hit[\'similarity\']:.2f}) '
               'to {_sg_hit.get(\'bucket\',\'?\')}: {_sg_hit[\'matched\'][:60]}", file=__import__("sys").stderr)')
    if new_imp in src:
        print("[emoclaw] already patched — skipping")
        return
    if old_imp not in src:
        print("[emoclaw] WARN: gate import not found — no change made")
        return
    shutil.copy(EMOCLAW, EMOCLAW + f".bak-{STAMP}")
    src = src.replace(old_imp, new_imp)
    if old_lbl in src:
        src = src.replace(old_lbl, new_lbl)
    open(EMOCLAW, "w").write(src)
    print("[emoclaw] express_want now calls check_want()")

if __name__ == "__main__":
    patch_gate()
    patch_emoclaw()
    print("DONE — restart the server / reimport for it to take effect.")
