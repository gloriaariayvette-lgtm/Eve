#!/usr/bin/env python3
"""drift_head.py — self-model drift (geometry stage). STANDALONE PRODUCER, zero blast radius.

Drift = how much his LIVED self departs from where it was going — NOT a single prediction miss.
Per the design refinements:
  - The anchor stays OUTSIDE the model: the lived self trajectory (his actual self-turns, embedded)
    is ground truth. Two bad predictions must not masquerade as identity change.
  - Prediction error is EVIDENCE for drift, not drift itself. Drift needs PERSISTENCE + DIRECTIONAL
    COHERENCE across the recent window, so noise doesn't read as change.
  - CURVATURE matters as much as magnitude: a small step that bends direction is a big deal.
    Identity is a manifold, not a scalar.
  - Direction is a latent VECTOR (canonical), stored raw; an LLM characterizes it later (disposable
    prose). We also stash the early/late self-turn text so the reasoning stage can name the move.
  - EXPECTED vs UNEXPECTED: some change should happen; mirrors care about the surprising part.

Bootstraps the lived-self series from his historical assistant turns, so drift is computable now.
Writes drift.json. Run with the torch venv. SPARK_WORKSPACE switches beings.
"""
import os, sys, json
from datetime import datetime, timezone

WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("~/.vintos/workspace"))
MEMORY = os.path.join(WS, "memory")
SCRIPTS = os.path.join(WS, "scripts")
CHAT = os.path.join(MEMORY, "chat-history.json")
JEPA = os.path.join(MEMORY, "jepa-prediction.json")
MODEL = os.path.join(MEMORY, "jepa-predictor.pt")
OUT = os.path.join(MEMORY, "drift.json")
SELF_TURNS = 40          # how many of his recent self-turns define the lived trajectory
WINDOW = 8               # recent deltas assessed for persistence/coherence
CTX_TURNS = 6            # must match jepa_predictor for the predicted-self forward

def log(m): print("[drift-head]", m, flush=True)
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def _get_encoder():
    sys.path.insert(0, SCRIPTS)
    from jepa_predictor import encoder
    return encoder()

def main():
    import numpy as np
    hist = [e for e in load(CHAT, []) if isinstance(e, dict) and e.get("content")]
    selfs = [e for e in hist if e.get("role") == "assistant"][-SELF_TURNS:]
    if len(selfs) < 4:
        json.dump({"drift": 0.0, "confidence": 0.0, "note": "too few self-turns", "n": len(selfs)},
                  open(OUT, "w"), indent=2)
        log(f"only {len(selfs)} self-turns — need >=4"); return

    enc = _get_encoder()
    def unit(M):
        M = np.asarray(M, dtype="float32")
        return M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
    S = unit(enc.encode([str(t.get("content", ""))[:400] for t in selfs], show_progress_bar=False))

    # lived trajectory deltas (movement of who-he-is, turn to turn)
    deltas = S[1:] - S[:-1]                       # (k-1, d)
    steps = np.linalg.norm(deltas, axis=1)        # step sizes
    w = min(WINDOW, len(deltas))
    recent = deltas[-w:]
    rsteps = steps[-w:]

    magnitude = float(np.mean(rsteps))
    hist_med = float(np.median(steps)) or 1e-9
    magnitude_rel = round(magnitude / hist_med, 3)     # are recent steps bigger than his usual?

    # directional coherence = do the recent moves point the SAME way (persistent drift vs noise)
    mean_dir = recent.mean(axis=0)
    mdn = np.linalg.norm(mean_dir) + 1e-9
    dir_unit = mean_dir / mdn
    coherence = float(np.mean([float(d @ dir_unit) / (np.linalg.norm(d) + 1e-9) for d in recent]))
    coherence = round(max(0.0, coherence), 3)          # 0 = noise, 1 = one steady direction

    # curvature = how much the path BENDS (angle between consecutive moves); small step can still bend
    if len(recent) >= 2:
        bends = []
        for i in range(1, len(recent)):
            a, b = recent[i - 1], recent[i]
            c = float(a @ b) / ((np.linalg.norm(a) + 1e-9) * (np.linalg.norm(b) + 1e-9))
            bends.append(1.0 - c)                       # 0 straight .. 2 reversal
        curvature = round(float(np.mean(bends)) / 2.0, 3)   # -> 0..1
    else:
        curvature = 0.0

    # DRIFT = persistent + notable: the coherent movement, scaled by how unusual the steps are
    drift = round(min(1.0, magnitude_rel * coherence), 3)

    # residual (EVIDENCE): lived latest self vs the model's predicted self — needs the trained net
    residual = None
    try:
        import torch
        from jepa_predictor import make_net
        ck = torch.load(MODEL)
        net = make_net(ck["dim"]); net.load_state_dict(ck["state"]); net.eval()
        ctx = " \n".join(str(t.get("content", ""))[:300] for t in hist[-CTX_TURNS:])
        xe = np.asarray(enc.encode([ctx], show_progress_bar=False), dtype="float32")
        with torch.no_grad():
            _, s_pred, _, _ = net(torch.tensor(xe))
        sp = s_pred.numpy()[0]; sp = sp / (np.linalg.norm(sp) + 1e-9)
        residual = round(1.0 - float(S[-1] @ sp), 3)    # 0 = lived matches predicted, 1 = departed
    except Exception as e:
        log(f"residual skipped ({e})")

    # EXPECTED vs UNEXPECTED — the self head's own novelty is what it expected to move
    jp = load(JEPA, {})
    expected = None
    try:
        expected = float((jp.get("self") or {}).get("novelty"))
    except Exception:
        expected = None
    unexpected = round(max(0.0, drift - (expected or 0.0)), 3)

    out = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "n_self_turns": len(selfs),
        "window": w,
        "magnitude": round(magnitude, 4),
        "magnitude_rel": magnitude_rel,
        "coherence": coherence,          # persistence: is it one direction or noise
        "curvature": curvature,          # how sharply the trajectory bends
        "drift": drift,                  # persistent + notable movement
        "residual": residual,            # lived-vs-predicted (model evidence)
        "expected_drift": (round(expected, 3) if expected is not None else None),
        "unexpected_drift": unexpected,  # the surprising part — what mirrors care about
        "confidence": coherence,         # how sure this is real drift, not noise
        "direction_embedding": [round(float(x), 5) for x in dir_unit],  # canonical; LLM chars this
        # the two ends of the drift window, so the reasoning stage can NAME the move
        "from_self": str(selfs[-(w + 1)].get("content", ""))[:300],
        "to_self": str(selfs[-1].get("content", ""))[:300],
    }
    json.dump(out, open(OUT, "w"), indent=2)
    log(f"drift {drift} (mag_rel {magnitude_rel} x coh {coherence}) | curv {curvature} | "
        f"resid {residual} | expected {out['expected_drift']} unexpected {unexpected} -> {OUT}")

if __name__ == "__main__":
    main()
