#!/usr/bin/env python3
"""pressure_head.py — the PRESSURE head. What Gloria was expected to say, and didn't emit.

Not "withheld" (accusatory) — PRESSURE: a predicted utterance that wasn't emitted, accumulating
until it deserves a voice. Reuses the JEPA gloria head, which already predicts her next-turn
embedding. When that prediction is RICH but her actual turn is SPARSE and DIVERGES from it,
something went unsaid — that gap is the pressure.

GUARDRAIL (load-bearing, from the design chat): this emits pressure magnitude + confidence + a VAGUE
shape gesture + a canonical direction vector. It NEVER reconstructs the unsaid sentence. "There was
something here," not "she almost said X." The moment it rebuilds exact unsaid thoughts it becomes a
completion engine and something is lost — sometimes the silence should stay silent.

  magnitude  = divergence(predicted, actual) x sparseness(actual)   — rich prediction, sparse reply
  confidence = how deliberate the omission looks (how sparse vs how much was expected)
  novelty    = is this a shape of unsaid she has not shown before (vs recent gap directions)
  shape      = nearest of a few coarse topic PROBES to the gap direction — a gesture, not the words

Accumulates into pressure.json; dreams consume when accumulated pressure crosses threshold ("what
has gathered enough pressure to deserve a voice"). Run with the torch venv. SPARK_WORKSPACE switches.
"""
import os, sys, json
from datetime import datetime, timezone

WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("~/.vintos/workspace"))
MEMORY = os.path.join(WS, "memory")
SCRIPTS = os.path.join(WS, "scripts")
CHAT = os.path.join(MEMORY, "chat-history.json")
MODEL = os.path.join(MEMORY, "jepa-predictor.pt")
OUT = os.path.join(MEMORY, "pressure.json")
CTX_TURNS = 6
RECENT_GLORIA = 6         # assess her most recent N turns
EXP_WORDS = 12.0          # a full turn ~ this many words; far fewer = sparse
# coarse shape probes — a GESTURE toward what went unsaid, never the words themselves
SHAPE_PROBES = {
    "closeness / being wanted": "closeness, being wanted, reaching for each other, wanting to be held",
    "desire / the body": "desire, the body, heat, wanting him physically",
    "the work / building": "the work, building, the architecture, what we are making",
    "something unresolved": "tension, something unresolved, a hesitation, holding back",
    "herself / her own day": "herself, her own day, her feelings, what she is carrying",
}

def log(m): print("[pressure-head]", m, flush=True)
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def parse_ts(x):
    try:
        d = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def sparseness(text):
    """How little she said vs a full turn. Very short reply -> near 1; a paragraph -> 0."""
    w = len((text or "").split())
    return round(max(0.0, 1.0 - w / EXP_WORDS), 3)

def pressure_of(divergence, sparse):
    return round(max(0.0, divergence) * sparse, 3)

def main():
    import numpy as np, torch
    sys.path.insert(0, SCRIPTS)
    from jepa_predictor import make_net, encoder
    if not os.path.exists(MODEL):
        log("no jepa model — train jepa_predictor first"); return
    hist = [e for e in load(CHAT, []) if isinstance(e, dict) and e.get("content")]
    if len(hist) < CTX_TURNS + 2:
        log("not enough history"); return

    ck = torch.load(MODEL); net = make_net(ck["dim"]); net.load_state_dict(ck["state"]); net.eval()
    enc = encoder()
    def emb(texts): return np.asarray(enc.encode(texts, show_progress_bar=False), dtype="float32")
    def unit(v): return v / (np.linalg.norm(v) + 1e-9)
    def cos(a, b): return float(unit(a) @ unit(b))

    probe_names = list(SHAPE_PROBES)
    probe_vecs = emb([SHAPE_PROBES[k] for k in probe_names])

    # her turns (role user), with their index so we can grab preceding context
    idxs = [i for i, e in enumerate(hist) if e.get("role") == "user" and i >= CTX_TURNS]
    idxs = idxs[-RECENT_GLORIA:]
    if not idxs:
        log("no assessable gloria turns"); return

    recent, gaps = [], []
    for i in idxs:
        ctx = " \n".join(str(hist[j].get("content", ""))[:300] for j in range(i - CTX_TURNS, i))
        actual_text = str(hist[i].get("content", ""))
        xe = emb([ctx])
        with torch.no_grad():
            g_pred, _, _, _ = net(torch.tensor(xe))
        pred = g_pred.numpy()[0]
        actual = emb([actual_text[:400]])[0]
        div = 1.0 - max(0.0, cos(pred, actual))         # predicted vs what she actually said
        sparse = sparseness(actual_text)
        press = pressure_of(div, sparse)
        gap = unit(pred) - unit(actual)                 # points toward the unsaid
        sims = [cos(gap, pv) for pv in probe_vecs]
        shape = probe_names[int(np.argmax(sims))] if press >= 0.12 else None
        rec = {"ts": hist[i].get("timestamp"), "pressure": press,
               "confidence": sparse,                     # deliberate-looking = said little when more expected
               "divergence": round(div, 3), "words": len(actual_text.split()),
               "shape": shape, "_gap": unit(gap).tolist()}
        recent.append(rec); gaps.append(unit(gap))

    # novelty: is the latest unsaid-shape new vs the earlier ones this window?
    for k, rec in enumerate(recent):
        if k == 0:
            rec["novelty"] = None
        else:
            prev = np.mean(gaps[:k], axis=0)
            rec["novelty"] = round(max(0.0, 1.0 - cos(gaps[k], prev)), 3)
        rec.pop("_gap", None)

    accumulated = round(sum(r["pressure"] for r in recent), 3)
    top = max(recent, key=lambda r: r["pressure"])
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accumulated_pressure": accumulated,             # dreams consume when this crosses threshold
        "peak": {"pressure": top["pressure"], "shape": top["shape"], "confidence": top["confidence"],
                 "novelty": top.get("novelty"), "ts": top["ts"]},
        "recent": recent,
        "note": "shape is a gesture toward the unsaid, never the words. there was something here.",
    }
    json.dump(out, open(OUT, "w"), indent=2)
    log(f"accumulated pressure {accumulated} over {len(recent)} turns -> {OUT}")
    log(f"  peak {top['pressure']} [{top['shape']}] conf {top['confidence']} — there was something here")

if __name__ == "__main__":
    main()
