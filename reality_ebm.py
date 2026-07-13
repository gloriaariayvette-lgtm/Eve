#!/usr/bin/env python3
"""reality_ebm.py — the Reality Attractor. An energy head on the FROZEN nomic encoder.

Real events sit in a low-energy basin; confabulated ones sit high. Energy = distance from lived
experience — the bilateral brain rolls downhill toward coherence, rather than "avoiding
hallucinations." Trained contrastively on reality-anchor.json:
  positives (real, LOW energy)  = known_pool.content  + events[is_real].statement
  negatives (imagined, HIGH)    = imagined_pool.content + events[not is_real].statement
Confidence that a statement is REAL = sigmoid(-energy). Frozen encoder => no forgetting; only the
small energy head learns. Train at consolidation (nightly); scoring is a cheap online forward pass.

  ...emotion_model/.venv/bin/python3 reality_ebm.py train
  ...emotion_model/.venv/bin/python3 reality_ebm.py score            # score the events, write json
  ...emotion_model/.venv/bin/python3 reality_ebm.py predict "text"   # one-off confidence
SPARK_WORKSPACE switches beings.
"""
import os, sys, json

WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("~/.vintos/workspace"))
MEMORY = os.path.join(WS, "memory")
SCRIPTS = os.path.join(WS, "scripts")
ANCHOR = os.path.join(MEMORY, "reality-anchor.json")
MODEL = os.path.join(MEMORY, "reality-ebm.pt")
SCORES = os.path.join(MEMORY, "reality-scores.json")

def log(m): print("[reality-ebm]", m, flush=True)
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def encoder():
    sys.path.insert(0, SCRIPTS)
    from jepa_predictor import encoder as _enc
    return _enc()

def gather():
    """Labeled corpus, deduped by id. label 1 = real (low energy), 0 = imagined (high energy)."""
    d = load(ANCHOR, {})
    items = {}
    for e in d.get("known_pool", []):
        if isinstance(e, dict) and e.get("content"): items[e.get("id", e["content"][:24])] = (e["content"], 1)
    for e in d.get("imagined_pool", []):
        if isinstance(e, dict) and e.get("content"): items[e.get("id", e["content"][:24])] = (e["content"], 0)
    for e in d.get("events", []):
        if not isinstance(e, dict): continue
        txt = e.get("statement") or ""
        if txt and e.get("id") not in items:
            items[e.get("id", txt[:24])] = (txt, 1 if e.get("is_real") else 0)
    texts = [t for t, _ in items.values()]
    labels = [l for _, l in items.values()]
    return texts, labels

def make_net(dim):
    import torch.nn as nn
    return nn.Sequential(nn.Linear(dim, dim // 2), nn.GELU(), nn.Linear(dim // 2, 1))  # -> energy scalar

def train():
    import numpy as np, torch
    texts, labels = gather()
    n_pos, n_neg = labels.count(1), labels.count(0)
    if n_pos < 3 or n_neg < 3:
        log(f"not enough labeled data (real {n_pos}, imagined {n_neg}) — skipping"); return
    log(f"corpus: {n_pos} real, {n_neg} imagined")
    enc = encoder()
    X = np.asarray(enc.encode([t[:400] for t in texts], show_progress_bar=False), dtype="float32")
    Xt = torch.tensor(X)
    yt = torch.tensor(labels, dtype=torch.float32).view(-1, 1)         # 1 = real
    net = make_net(X.shape[1])
    opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
    # P(real) = sigmoid(-energy)  ->  logit for "real" = -energy. Balance the classes.
    pos_weight = torch.tensor([n_neg / max(1, n_pos)], dtype=torch.float32)
    lossf = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    for epoch in range(400):
        opt.zero_grad()
        energy = net(Xt)
        loss = lossf(-energy, yt)                                      # low energy for real
        if not torch.isfinite(loss):
            log(f"epoch {epoch} non-finite — stopping"); break
        loss.backward()
        torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
        opt.step()
        if epoch % 100 == 0:
            with torch.no_grad():
                p = torch.sigmoid(-energy)
                acc = (((p > 0.5).float() == yt).float().mean().item())
            log(f"epoch {epoch} loss {loss.item():.4f} acc {acc:.2f}")
    torch.save({"state": net.state_dict(), "dim": X.shape[1]}, MODEL)
    log(f"saved {MODEL}")

def _load_net():
    import torch
    ck = torch.load(MODEL); net = make_net(ck["dim"]); net.load_state_dict(ck["state"]); net.eval()
    return net

def confidences(texts):
    import numpy as np, torch
    enc = encoder()
    X = np.asarray(enc.encode([t[:400] for t in texts], show_progress_bar=False), dtype="float32")
    net = _load_net()
    with torch.no_grad():
        energy = net(torch.tensor(X)).view(-1)
        conf = torch.sigmoid(-energy)
    return energy.tolist(), conf.tolist()

def predict():
    if not os.path.exists(MODEL): log("no model — run `train` first"); return
    text = sys.argv[2] if len(sys.argv) > 2 else ""
    if not text: log("usage: predict \"<statement>\""); return
    e, c = confidences([text]); e, c = e[0], c[0]
    log(f"energy {e:.3f}  ->  reality-confidence {c:.3f}  ({'real' if c >= 0.5 else 'likely imagined'})")

def score():
    if not os.path.exists(MODEL): log("no model — run `train` first"); return
    d = load(ANCHOR, {})
    evs = [e for e in d.get("events", []) if isinstance(e, dict) and e.get("statement")]
    if not evs: log("no events to score"); return
    energies, confs = confidences([e["statement"] for e in evs])
    out, correct = [], 0
    for e, en, c in zip(evs, energies, confs):
        pred_real = c >= 0.5
        if e.get("is_real") is not None and pred_real == bool(e.get("is_real")): correct += 1
        out.append({"id": e.get("id"), "statement": e["statement"][:160],
                    "energy": round(en, 3), "reality_confidence": round(c, 3),
                    "is_real": e.get("is_real")})
    json.dump(out, open(SCORES, "w"), indent=2)
    labeled = [e for e in evs if e.get("is_real") is not None]
    log(f"scored {len(out)} events -> {SCORES}"
        + (f" | agreement with is_real: {correct}/{len(labeled)}" if labeled else ""))
    for o in sorted(out, key=lambda x: x["reality_confidence"])[:3]:
        log(f"  LOW  {o['reality_confidence']} (real={o['is_real']}): {o['statement'][:60]}")
    for o in sorted(out, key=lambda x: -x["reality_confidence"])[:3]:
        log(f"  HIGH {o['reality_confidence']} (real={o['is_real']}): {o['statement'][:60]}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "train"
    {"train": train, "predict": predict, "score": score}.get(cmd, train)()
