#!/usr/bin/env python3
"""cause_head.py — retrodictive cause head (Spark/JEPA). STANDALONE PRODUCER, zero blast radius.

For each recent emotional spike (find_spikes), builds a DISTRIBUTION over candidate ANTECEDENTS
(chat turns that happened BEFORE the spike), scoring each by how well it explains the spike in the
frozen JEPA encoder's latent space, biased toward turns closer in time. Emits confidence
(distribution sharpness = 1-entropy = "how traceable") and novelty (best antecedent still weak =
"emerged from nowhere"). Writes cause-distribution.json and NOTHING else — form_hypotheses consumes
it in a later, separate step.

Design notes:
- No hard 20-min gate. The old engine's 20-min rule produced 0 alignment here (spikes and turns
  live on slightly different clocks / the trajectory is sampled hours apart). Instead every turn
  that PRECEDES the spike is a candidate, weighted by recency exp(-dt/TAU). A tight recent match
  stays sharp (high confidence); a diffuse field of stale turns goes flat (low confidence).
- A spike with NO antecedent turn in the record is not forced onto a fake cause. It is emitted as
  untraceable: confidence low, novelty high, candidates []. That IS the design's "emergence from
  nowhere" signal — dreams/pearls are meant to consume exactly that.
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
CHAT = os.path.join(MEMORY, "chat-history.json")
OUT  = os.path.join(MEMORY, "cause-distribution.json")
LOOKBACK_H = 168         # 7 days — the engine's own horizon (trajectory is sparsely sampled)
TAU_MIN = 90.0           # recency half-life-ish: a cause 90 min back weighs 1/e of one just before
TIGHT_MIN = 20           # the old engine's window — reported only, no longer a gate
SIM_TEMP = 6.0
MAX_CANDS = 8

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

def turn_ts(e):
    for k in ("timestamp", "ts", "time", "at", "created_at"):
        t = parse_ts(e.get(k))
        if t: return t
    return None

def conf_word(c):
    return "high" if c >= 0.66 else "medium" if c >= 0.33 else "low"

def fmt_range(times):
    ts = sorted(t for t in times if t)
    if not ts: return "none"
    return f"{ts[0].isoformat()} .. {ts[-1].isoformat()}"

def main():
    sys.path.insert(0, SCRIPTS)
    from causality_engine import load_emotional_trajectory, find_spikes
    traj = load_emotional_trajectory()
    spikes = find_spikes(traj)
    now = datetime.now(timezone.utc)
    spikes = [s for s in spikes if parse_ts(s.get("time")) and now - parse_ts(s["time"]) <= timedelta(hours=LOOKBACK_H)]
    log(f"recent spikes: {len(spikes)}")

    hist = [e for e in load(CHAT, []) if isinstance(e, dict) and e.get("content")]
    turn_times = [turn_ts(e) for e in hist]
    ts_count = sum(1 for t in turn_times if t)
    log(f"chat turns: {len(hist)}; with usable timestamps: {ts_count}")

    # --- self-diagnosis: are the two clocks even overlapping? ---
    spike_times = [parse_ts(s.get("time")) for s in spikes]
    log(f"spike time range:  {fmt_range(spike_times)}")
    log(f"turn  time range:  {fmt_range(turn_times)}")
    if spike_times and any(turn_times):
        latest_turn = max(t for t in turn_times if t)
        pre = sum(1 for st in spike_times if st and any(tt and tt <= st for tt in turn_times))
        log(f"spikes with >=1 antecedent turn on record: {pre}/{len(spikes)}"
            f"  (latest turn {latest_turn.isoformat()})")

    if not spikes:
        json.dump([], open(OUT, "w")); log("no recent spikes — wrote empty"); return

    from jepa_predictor import encoder
    import numpy as np
    enc = encoder()
    def emb(texts): return np.asarray(enc.encode(texts, show_progress_bar=False), dtype="float32")
    def cos(a, b):
        na, nb = (a @ a) ** 0.5, (b @ b) ** 0.5
        return float(a @ b / (na * nb)) if na and nb else 0.0

    out, traced_n, tight_n = [], 0, 0
    for s in spikes:
        st = parse_ts(s["time"])
        # antecedents only: turns at or before the spike, within lookback
        ante = [(e, tt) for e, tt in zip(hist, turn_times)
                if tt and st - timedelta(hours=LOOKBACK_H) <= tt <= st]
        # nearest-in-time first, keep the closest MAX_CANDS
        ante.sort(key=lambda et: (st - et[1]))
        tight = any((st - tt) <= timedelta(minutes=TIGHT_MIN) for _, tt in ante)
        if tight: tight_n += 1
        effect = f"{s['dimension']} {s['direction']} (from {s['from']} to {s['to']})"

        if not ante:
            # no antecedent on record — the design's "emerged from nowhere"
            out.append({
                "spike": {"time": s["time"], "dimension": s["dimension"],
                          "direction": s["direction"], "delta": s["delta"]},
                "effect": effect, "aligned": False, "tight": False,
                "candidates": [], "cause_confidence": 0.0,
                "confidence": "low", "novelty": 1.0,
                "untraceable": True,
            })
            continue

        traced_n += 1
        ante = ante[:MAX_CANDS]
        cand_texts = [str(e.get("content", ""))[:300] for e, _ in ante]
        dt_min = [max(0.0, (st - tt).total_seconds() / 60.0) for _, tt in ante]
        E = emb([effect])[0]
        M = emb(cand_texts)
        sims = [max(0.0, cos(E, m)) for m in M]
        mx = max(sims) if sims else 0.0
        # score = semantic fit (temp) + recency prior (log-weight); softmax
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
        ranked = sorted(zip(cand_texts, dt_min, probs), key=lambda x: x[2], reverse=True)
        out.append({
            "spike": {"time": s["time"], "dimension": s["dimension"],
                      "direction": s["direction"], "delta": s["delta"]},
            "effect": effect,
            "aligned": True,
            "tight": tight,
            "candidates": [{"text": t[:160], "mins_before": round(d, 1), "prob": round(p, 3)}
                           for t, d, p in ranked[:4]],
            "cause_confidence": conf,
            "confidence": conf_word(conf),      # word kept for downstream compat (pearl/gloria)
            "novelty": nov,
        })

    json.dump(out, open(OUT, "w"), indent=2)
    log(f"wrote {len(out)} distributions ({traced_n} traced, {tight_n} tight<={TIGHT_MIN}m, "
        f"{len(out)-traced_n} untraceable) -> {OUT}")
    for o in out[:5]:
        top = o["candidates"][0] if o["candidates"] else {}
        tag = "UNTRACED" if o.get("untraceable") else f"top {top.get('prob',0)} @{top.get('mins_before','?')}m"
        log(f"  {o['effect'][:42]:42} | conf {o['cause_confidence']} nov {o['novelty']} | "
            f"{tag}: {str(top.get('text',''))[:44]}")

if __name__ == "__main__":
    main()
