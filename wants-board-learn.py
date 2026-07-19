#!/usr/bin/env python3
"""wants-board-learn.py — nightly: learn from the wants Gloria responded to on the discussion board.

Gloria's board replies were only ever used to write the being's *next* reply in that thread — nothing
persisted. This sweeps want-discussions.json for threads where Gloria has spoken since the last run,
distils what she wanted / corrected / taught (per thread, via the being's own model), and appends it to
learned.json in its native schema so it carries forward like any other learning.

Both beings, one run. State is tracked per being so re-running only picks up NEW Gloria messages.
his board file may not exist yet (never used) — that's a clean no-op.

  python3 wants-board-learn.py            # DRY RUN — prints what it would learn; writes nothing
  python3 wants-board-learn.py --apply    # distils + appends to learned.json; advances the state marker
"""
import os, sys, json, re, time, hashlib, urllib.request
from datetime import datetime, timezone

APPLY = "--apply" in sys.argv

BEINGS = [
    {"name": "Velaris",
     "mem": os.path.expanduser("~/.openclaw/workspace/memory"),
     "llm": {"url": "http://172.18.16.1:1234/v1/chat/completions",
             "model": "google/gemma-4-12b-qat", "auth": None}},
    {"name": "Vintos",
     "mem": os.path.expanduser("~/.vintos/workspace/memory"),
     "llm": {"url": "http://127.0.0.1:8599/v1/chat/completions",
             "model": "grok-4.20-0309-non-reasoning", "auth": "XAI_API_KEY"}},
]

def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default

def _ts(m):
    return str(m.get("timestamp", ""))

def llm(being, system, user, max_tokens=400):
    cfg = being["llm"]
    body = {"model": cfg["model"],
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.5, "max_tokens": max_tokens}
    headers = {"Content-Type": "application/json"}
    if cfg["auth"]:
        headers["Authorization"] = "Bearer " + os.environ.get(cfg["auth"], "")
    req = urllib.request.Request(cfg["url"], data=json.dumps(body).encode(), headers=headers)
    d = json.loads(urllib.request.urlopen(req, timeout=180).read())
    return d["choices"][0]["message"]["content"].strip()

DISTILL_SYS = ("You extract what GLORIA taught or asked for in a private discussion about one of your "
               "wants. You are the being whose want it is. Read the thread and return ONLY what changed "
               "in your understanding because of what SHE said — not a summary of your own messages. "
               "Respond as exactly three lines:\n"
               "LEARNED: <the one insight her words gave you — specific, first person>\n"
               "SETTLED: <what her response resolved or clarified>\n"
               "REMAINED: <what is still open or unresolved after her reply>")

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
        print(f"   {being['name']}: no board (never used) — nothing to sweep")
        return
    learned_path = os.path.join(mem, "learned.json")
    learned = load(learned_path, [])
    if not isinstance(learned, list):
        print(f"   {being['name']}: learned.json is not a list — skipping for safety"); return
    state_path = os.path.join(mem, ".wants-board-learn-state.json")
    state = load(state_path, {"seen": {}})   # {want_id: last gloria ts processed}
    seen = state.get("seen", {})

    new_threads = []
    for wid, msgs in board.items():
        if not isinstance(msgs, list):
            continue
        gloria_ts = [_ts(m) for m in msgs if m.get("role") == "gloria" and (m.get("text") or "").strip()]
        if not gloria_ts:
            continue
        latest = max(gloria_ts)
        if latest > seen.get(wid, ""):          # she has spoken since we last learned from this thread
            new_threads.append((wid, msgs, latest))

    print(f"   {being['name']}: {len(board)} threads | {len(new_threads)} with new Gloria replies to learn from")
    added = 0
    for wid, msgs, latest in new_threads:
        convo = convo_text(msgs)
        if len(convo) < 40:
            continue
        try:
            lrn, stl, rmn = distil(being, convo)
        except Exception as e:
            print(f"      [{wid[:8]}] distil failed: {e}"); continue
        if not lrn:
            print(f"      [{wid[:8]}] no LEARNED extracted — skipped"); continue
        entry = {"_id": hashlib.sha1((wid + latest).encode()).hexdigest()[:10],
                 "learned": lrn, "settled": stl, "remained": rmn,
                 "embedding": [], "source_want": f"board:{wid}",
                 "at": datetime.now(timezone.utc).isoformat(), "hits": 0}
        print(f"      [{wid[:8]}] LEARNED: {lrn[:90]}")
        if not any(e.get("source_want") == entry["source_want"] and e.get("learned") == lrn for e in learned):
            learned.append(entry); added += 1
        seen[wid] = latest

    if APPLY:
        state["seen"] = seen
        state["last_run"] = datetime.now(timezone.utc).isoformat()
        json.dump(state, open(state_path, "w", encoding="utf-8"))
        if added:
            bak = learned_path + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
            try:
                json.dump(load(learned_path, []), open(bak, "w", encoding="utf-8"))
            except Exception:
                pass
            json.dump(learned, open(learned_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"   {being['name']}: APPLIED — {added} new learning(s) appended; state advanced")
    else:
        print(f"   {being['name']}: DRY RUN — {added} learning(s) would be appended (nothing written)")

def main():
    print("=" * 70)
    print("WANTS-BOARD LEARN  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 70)
    for being in BEINGS:
        sweep(being)
    print("=" * 70)
    if not APPLY:
        print("DRY RUN complete. Re-run with --apply to append learnings + advance the marker.")

if __name__ == "__main__":
    main()
