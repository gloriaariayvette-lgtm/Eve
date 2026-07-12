#!/usr/bin/env python3
"""cause_head.py — retrodictive cause head (Spark/JEPA). STANDALONE PRODUCER, zero blast radius.

For each recent emotional spike (find_spikes), builds a DISTRIBUTION over candidate ANTECEDENTS —
events that happened BEFORE the spike — scoring each by how well it explains the spike in the
frozen JEPA encoder's latent space, biased toward events closer in time. Emits confidence
(distribution sharpness = 1-entropy = "how traceable") and novelty (best antecedent still weak =
"emerged from nowhere"). Writes cause-distribution.json and NOTHING else — form_hypotheses consumes
it in a later, separate step.

Antecedents are drawn from a UNION of sources, not just chat: his conversations AND his inner
life (gallery walks, unfinished threads, wants, relationship shifts). Overnight spikes have no
chat near them — their real cause is something he did while she slept — so each candidate carries
a `source` tag and the head can trace a 5am arousal spike to a 4:50am gallery walk instead of
last night's small talk.

Design notes:
- No hard time gate. Every event that PRECEDES the spike is a candidate, weighted by recency
  exp(-dt/TAU). A tight recent match stays sharp (high confidence); a diffuse field of stale
  events goes flat (low confidence).
- A spike with NO antecedent on record is emitted untraceable (conf low, novelty high,
  candidates []). That IS the design's "emergence from nowhere" — dreams/pearls consume it.
- Keeps a word-confidence (high/medium/low) alongside the float so downstream (pearl trigger,
  gloria record) stays compatible when we wire consumption.

Run with the torch venv: ...emotion_model/.venv/bin/python3 cause_head.py
SPARK_WORKSPACE switches beings.
"""
import os, sys, json, math
from datetime import datetime, timezone, timedelta

WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("~/.vintos/workspace"))
MEMORY = os.path.join(WS, "memory")
SCRIPTS = os.path.join(WS, "scripts")
OUT  = os.path.join(MEMORY, "cause-distribution.json")
LOOKBACK_H = 168         # 7 days — the engine's own horizon (trajectory is sparsely sampled)
TAU_MIN = 90.0           # recency half-life-ish: a cause 90 min back weighs 1/e of one just before
TIGHT_MIN = 20           # the old engine's window — reported only, no longer a gate
SIM_TEMP = 6.0
MAX_CANDS = 8

TSKEYS = ("timestamp", "ts", "time", "at", "created_at", "audited_at", "generated_at")
# source tag, filename, text fields to join (in priority order)
SOURCES = [
    ("chat",     "chat-history.json",        ("content",)),
    ("gallery",  "gallery-walks.json",       ("reflection", "saw")),
    ("thread",   "unfinished-threads.json",  ("thread",)),
    ("want",     "current-wants.json",       ("want",)),
    ("relation", "relationship-history.json",("shift", "trajectory")),
]

def log(m): print("[cause-head]", m, flush=True)
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def parse_ts(x):
    if x is None: return None
    if isinstance(x, (int, float)):
        try: return datetime.fromtimestamp(x, timezone.utc)
        except Exception: return None
    try:
        d = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception: return None

def entry_ts(e):
    for k in TSKEYS:
        t = parse_ts(e.get(k))
        if t: return t
    return None

def conf_word(c):
    return "high" if c >= 0.66 else "medium" if c >= 0.33 else "low"

def fmt_range(times):
    ts = sorted(t for t in times if t)
    if not ts: return "none"
    return f"{ts[0].isoformat()} .. {ts[-1].isoformat()}"

def collect_events():
    """Union of timestamped text events across chat + inner-life logs."""
    events, per_src = [], {}
    for src, fname, textkeys in SOURCES:
        d = load(os.path.join(MEMORY, fname), [])
        if not isinstance(d, list): continue
        n = 0
        for e in d:
            if not isinstance(e, dict): continue
            ts = entry_ts(e)
            if not ts: continue
            parts = []
            for k in textkeys:
                v = e.get(k)
                if v: parts.append(str(v))
            text = " ".join(parts).strip()
            if not text: continue
            events.append({"ts": ts, "source": src, "text": text[:300]})
            n += 1
        per_src[src] = n
    return events, per_src

def main():
    sys.path.insert(0, SCRIPTS)
    from causality_engine import load_emotional_trajectory, find_spikes
    traj = load_emotional_trajectory()
    spikes = find_spikes(traj)
    now = datetime.now(timezone.utc)
    spikes = [s for s in spikes if parse_ts(s.get("time")) and now - parse_ts(s["time"]) <= timedelta(hours=LOOKBACK_H)]
    log(f"recent spikes: {len(spikes)}")

    events, per_src = collect_events()
    log(f"candidate events: {len(events)}  " + ", ".join(f"{k}:{v}" for k, v in per_src.items()))

    # --- self-diagnosis: do the clocks overlap? ---
    spike_times = [parse_ts(s.get("time")) for s in spikes]
    ev_times = [e["ts"] for e in events]
    log(f"spike time range:  {fmt_range(spike_times)}")
    log(f"event time range:  {fmt_range(ev_times)}")
    if spike_times and ev_times:
        pre = sum(1 for st in spike_times if st and any(t <= st for t in ev_times))
        log(f"spikes with >=1 antecedent event on record: {pre}/{len(spikes)}")

    if not spikes:
        json.dump([], open(OUT, "w")); log("no recent spikes — wrote empty"); return
    if not events:
        json.dump([], open(OUT, "w")); log("no candidate events — wrote empty"); return

    from jepa_predictor import encoder
    import numpy as np
    enc = encoder()
    def emb(texts): return np.asarray(enc.encode(texts, show_progress_bar=False), dtype="float32")
    def cos(a, b):
        na, nb = (a @ a) ** 0.5, (b @ b) ** 0.5
        return float(a @ b / (na * nb)) if na and nb else 0.0

    # embed every event once; reuse across spikes
    EV = emb([e["text"] for e in events])
    for e, v in zip(events, EV): e["_v"] = v

    out, traced_n, tight_n = [], 0, 0
    for s in spikes:
        st = parse_ts(s["time"])
        lo = st - timedelta(hours=LOOKBACK_H)
        ante = [e for e in events if lo <= e["ts"] <= st]
        ante.sort(key=lambda e: (st - e["ts"]))            # nearest first
        tight = any((st - e["ts"]) <= timedelta(minutes=TIGHT_MIN) for e in ante)
        if tight: tight_n += 1
        effect = f"{s['dimension']} {s['direction']} (from {s['from']} to {s['to']})"

        if not ante:
            out.append({
                "spike": {"time": s["time"], "dimension": s["dimension"],
                          "direction": s["direction"], "delta": s["delta"]},
                "effect": effect, "aligned": False, "tight": False,
                "candidates": [], "cause_confidence": 0.0,
                "confidence": "low", "novelty": 1.0, "untraceable": True,
            })
            continue

        traced_n += 1
        ante = ante[:MAX_CANDS]
        E = emb([effect])[0]
        sims = [max(0.0, cos(E, e["_v"])) for e in ante]
        dt_min = [max(0.0, (st - e["ts"]).total_seconds() / 60.0) for e in ante]
        mx = max(sims) if sims else 0.0
        scores = [sims[i] * SIM_TEMP + math.log(math.exp(-dt_min[i] / TAU_MIN) + 1e-9)
                  for i in range(len(sims))]
        smax = max(scores)
        exps = [math.exp(x - smax) for x in scores]
        Z = sum(exps) or 1.0
        probs = [e / Z for e in exps]
        H = -sum(p * math.log(p + 1e-9) for p in probs)
        Hmax = math.log(len(probs)) if len(probs) > 1 else 1.0
        conf = round(1 - (H / Hmax if Hmax else 0.0), 3)   # sharp distribution = traceable
        nov = round(1 - mx, 3)                              # no good antecedent = emergence
        ranked = sorted(zip(ante, dt_min, probs), key=lambda x: x[2], reverse=True)
        out.append({
            "spike": {"time": s["time"], "dimension": s["dimension"],
                      "direction": s["direction"], "delta": s["delta"]},
            "effect": effect, "aligned": True, "tight": tight,
            "candidates": [{"source": e["source"], "text": e["text"][:160],
                            "mins_before": round(d, 1), "prob": round(p, 3)}
                           for e, d, p in ranked[:4]],
            "cause_confidence": conf,
            "confidence": conf_word(conf),      # word kept for downstream compat (pearl/gloria)
            "novelty": nov,
        })

    json.dump(out, open(OUT, "w"), indent=2)
    log(f"wrote {len(out)} distributions ({traced_n} traced, {tight_n} tight<={TIGHT_MIN}m, "
        f"{len(out)-traced_n} untraceable) -> {OUT}")
    for o in out[:6]:
        top = o["candidates"][0] if o["candidates"] else {}
        tag = "UNTRACED" if o.get("untraceable") else \
              f"[{top.get('source','?')}] p{top.get('prob',0)} @{top.get('mins_before','?')}m"
        log(f"  {o['effect'][:40]:40} | conf {o['cause_confidence']} nov {o['novelty']} | "
            f"{tag}: {str(top.get('text',''))[:40]}")

if __name__ == "__main__":
    main()
