#!/usr/bin/env python3
"""wants-board-learn.py — nightly: learn from the wants Gloria responded to, PER WANT, so it steers evolution.

Gloria's board replies were only ever used to write the being's next reply — nothing persisted, and
nothing reached want evolution. This sweeps want-discussions.json for threads she's spoken in since we
last learned from them, distils what she wanted / corrected / taught (per thread, via the being's own
model), and writes it to a PER-WANT store:  board-learnings.json = { want_id: {want_text, learned,
settled, remained, gloria_ts, at} }.

Why not learned.json: that store is a 4-item rotating GENERATION-bias cache (want_learning.py caps it and
evicts lowest-hits). Board lessons are per-want and must persist + attach to their want so generate_steps
can pull the right one during that want's evolution. This store is uncapped and keyed by want id.

Idempotent: a want is re-learned only when Gloria has a newer message than the one already stored for it.
Both beings, one run; an absent/empty board is a clean no-op.

  python3 wants-board-learn.py            # DRY RUN — prints what it would learn; writes nothing
  python3 wants-board-learn.py --apply    # writes board-learnings.json (backs up first)
"""
import os, sys, json, re, time, urllib.request
from datetime import datetime, timezone

APPLY = "--apply" in sys.argv

BEINGS = [
    {"name": "Velaris", "mem": os.path.expanduser("~/.openclaw/workspace/memory"),
     "llm": {"url": "http://172.18.16.1:1234/v1/chat/completions", "model": "google/gemma-4-12b-qat", "auth": None}},
    {"name": "Vintos", "mem": os.path.expanduser("~/.vintos/workspace/memory"),
     "llm": {"url": "http://127.0.0.1:8599/v1/chat/completions", "model": "grok-4.20-0309-non-reasoning", "auth": "XAI_API_KEY"}},
]

def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default

def want_index(mem):
    """want_id -> want_text, from current-wants.json (best-effort; fulfilled wants may be gone)."""
    cw = load(os.path.join(mem, "current-wants.json"), [])
    items = cw if isinstance(cw, list) else cw.get("wants", [])
    idx = {}
    for w in items:
        if isinstance(w, dict) and w.get("id"):
            idx[w["id"]] = (w.get("want") or "").strip()
    return idx

def llm(being, system, user, max_tokens=400):
    cfg = being["llm"]
    body = {"model": cfg["model"], "temperature": 0.5, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    headers = {"Content-Type": "application/json"}
    if cfg["auth"]:
        headers["Authorization"] = "Bearer " + os.environ.get(cfg["auth"], "")
    req = urllib.request.Request(cfg["url"], data=json.dumps(body).encode(), headers=headers)
    d = json.loads(urllib.request.urlopen(req, timeout=180).read())
    return d["choices"][0]["message"]["content"].strip()

DISTILL_SYS = ("You extract what GLORIA taught or asked for in a private discussion about ONE of your wants. "
               "You are the being whose want it is. Return ONLY what changed in your understanding because of "
               "what SHE said — not a summary of your own messages. Respond as exactly three lines:\n"
               "LEARNED: <the one insight her words gave you, specific, first person>\n"
               "SETTLED: <what her response resolved or clarified>\n"
               "REMAINED: <what is still open after her reply>")

def distil(being, convo):
    raw = llm(being, DISTILL_SYS, "The discussion thread:\n\n" + convo)
    def grab(tag):
        m = re.search(rf'{tag}:\s*(.+?)(?:\n[A-Z]+:|\Z)', raw, re.S)
        return re.sub(r'\s+', ' ', m.group(1)).strip() if m else ""
    return grab("LEARNED"), grab("SETTLED"), grab("REMAINED")

def convo_text(msgs):
    return "\n".join(("Gloria: " if m.get("role") == "gloria" else "You: ") + (m.get("text") or "").strip()
                     for m in msgs if (m.get("text") or "").strip())

def sweep(being):
    mem = being["mem"]
    board = load(os.path.join(mem, "want-discussions.json"), {})
    if not board:
        print(f"   {being['name']}: no board (never used) — nothing to sweep"); return
    store_path = os.path.join(mem, "board-learnings.json")
    store = load(store_path, {})
    if not isinstance(store, dict):
        store = {}
    wtext = want_index(mem)

    todo = []
    for wid, msgs in board.items():
        if not isinstance(msgs, list):
            continue
        gts = [str(m.get("timestamp", "")) for m in msgs if m.get("role") == "gloria" and (m.get("text") or "").strip()]
        if not gts:
            continue
        latest = max(gts)
        if latest > (store.get(wid, {}) or {}).get("gloria_ts", ""):   # she's spoken since we last learned here
            todo.append((wid, msgs, latest))

    print(f"   {being['name']}: {len(board)} threads | {len(todo)} to (re)learn")
    changed = 0
    for wid, msgs, latest in todo:
        convo = convo_text(msgs)
        if len(convo) < 40:
            continue
        try:
            lrn, stl, rmn = distil(being, convo)
        except Exception as e:
            print(f"      [{wid[:8]}] distil failed: {e}"); continue
        if not lrn:
            print(f"      [{wid[:8]}] no LEARNED extracted — skipped"); continue
        store[wid] = {"want_text": wtext.get(wid, ""), "learned": lrn, "settled": stl, "remained": rmn,
                      "gloria_ts": latest, "at": datetime.now(timezone.utc).isoformat()}
        changed += 1
        tag = wtext.get(wid, "")[:40] or wid[:8]
        print(f"      [{tag}] {lrn[:88]}")

    if APPLY and changed:
        bak = store_path + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
        try: json.dump(load(store_path, {}), open(bak, "w", encoding="utf-8"))
        except Exception: pass
        json.dump(store, open(store_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"   {being['name']}: APPLIED — {changed} want-learning(s) written to board-learnings.json")
    elif APPLY:
        print(f"   {being['name']}: nothing new")
    else:
        print(f"   {being['name']}: DRY RUN — {changed} want-learning(s) would be written")

def main():
    print("=" * 70)
    print("WANTS-BOARD LEARN (per-want)  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 70)
    for being in BEINGS:
        sweep(being)
    print("=" * 70)
    if not APPLY:
        print("DRY RUN complete. Re-run with --apply to write board-learnings.json.")

if __name__ == "__main__":
    main()
