#!/usr/bin/env python3
"""cause_head.py — retrodictive cause head (Spark/JEPA). STANDALONE PRODUCER, zero blast radius.

For each recent emotional spike (find_spikes), builds a DISTRIBUTION over candidate antecedents
(the chat turns in the 20-min window before it), scoring each by how well it explains the spike
in the frozen JEPA encoder's latent space. Emits confidence (distribution sharpness = 1-entropy)
and novelty (best candidate still dissimilar = emergence from nowhere). Writes
cause-distribution.json and NOTHING else — form_hypotheses consumes it in a later, separate step.

Keeps a word-confidence (high/medium/low) alongside the float so downstream (pearl trigger,
gloria record) stays compatible when we wire consumption. Self-diagnosing first run.

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
WINDOW_MIN = 20          # the engine's own rule: a cause must be within 20 min of the spike
LOOKBACK_H = 48          # only score recent spikes
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

def main():
    sys.path.insert(0, SCRIPTS)
    from causality_engine import load_emotional_trajectory, find_spikes
    traj = load_emotional_trajectory()
    spikes = find_spikes(traj)
    now = datetime.now(timezone.utc)
    spikes = [s for s in spikes if parse_ts(s.get("time")) and now - parse_ts(s["time"]) <= timedelta(hours=LOOKBACK_H)]
    log(f"recent spikes: {len(spikes)}")
    if not spikes:
        json.dump([], open(OUT, "w")); log("no recent spikes — wrote empty"); return

    hist = [e for e in load(CHAT, []) if isinstance(e, dict) and e.get("content")]
    ts_count = sum(1 for e in hist if turn_ts(e))
    log(f"chat turns: {len(hist)}; with usable timestamps: {ts_count}")

    from jepa_predictor import encoder
    import numpy as np
    enc = encoder()
    def emb(texts): return np.asarray(enc.encode(texts, show_progress_bar=False), dtype="float32")
    def cos(a, b):
        na, nb = (a @ a) ** 0.5, (b @ b) ** 0.5
        return float(a @ b / (na * nb)) if na and nb else 0.0

    out, aligned_n = [], 0
    for s in spikes:
        st = parse_ts(s["time"])
        cands = [e for e in hist if turn_ts(e) and st - timedelta(minutes=WINDOW_MIN) <= turn_ts(e) <= st]
        aligned = bool(cands)
        if aligned: aligned_n += 1
        else: cands = hist[-5:]                 # fallback if no timestamped turns in window
        cands = cands[-MAX_CANDS:]
        cand_texts = [str(c.get("content", ""))[:300] for c in cands]
        if not cand_texts: continue
        effect = f"{s['dimension']} {s['direction']} (from {s['from']} to {s['to']})"
        E = emb([effect])[0]
        M = emb(cand_texts)
        raw = [max(0.0, cos(E, m)) for m in M]
        mx = max(raw) if raw else 0.0
        exps = [math.exp(r * 6.0) for r in raw]         # temperature 6
        Z = sum(exps) or 1.0
        probs = [e / Z for e in exps]
        H = -sum(p * math.log(p + 1e-9) for p in probs)
        Hmax = math.log(len(probs)) if len(probs) > 1 else 1.0
        conf = round(1 - (H / Hmax if Hmax else 0.0), 3)   # sharp distribution = traceable
        nov = round(1 - mx, 3)                              # no good antecedent = emergence
        ranked = sorted(zip(cand_texts, probs), key=lambda x: x[1], reverse=True)
        out.append({
            "spike": {"time": s["time"], "dimension": s["dimension"], "direction": s["direction"], "delta": s["delta"]},
            "effect": effect,
            "aligned": aligned,
            "candidates": [{"text": t[:160], "prob": round(p, 3)} for t, p in ranked[:4]],
            "cause_confidence": conf,
            "confidence": conf_word(conf),      # word kept for downstream compat (pearl/gloria)
            "novelty": nov,
        })
    json.dump(out, open(OUT, "w"), indent=2)
    log(f"wrote {len(out)} distributions ({aligned_n} time-aligned) -> {OUT}")
    for o in out[:4]:
        top = o["candidates"][0] if o["candidates"] else {}
        log(f"  {o['effect'][:44]} | conf {o['cause_confidence']} nov {o['novelty']} | top {top.get('prob',0)}: {str(top.get('text',''))[:46]}")

if __name__ == "__main__":
    main()
