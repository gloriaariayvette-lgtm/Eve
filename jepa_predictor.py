#!/usr/bin/env python3
"""jepa_predictor.py — a small, runnable JEPA-lite over conversation embeddings.

FROZEN encoder (nomic-embed via sentence_transformers) -> a tiny predictor MLP that
predicts the EMBEDDING of the next turn from a context window. Self-supervised on
chat-history (the next turn IS the target; no labels needed). One shared trunk, two
heads (self / gloria) = one latent space, per Eve's note. Outputs prediction +
confidence (heteroscedastic variance head) + novelty (how far the forecast moves
from the current context). Freezing the encoder sidesteps representation collapse.

Run with the torch venv:
  ~/.vintos/workspace/emotion_model/.venv/bin/python3 jepa_predictor.py train
  ~/.vintos/workspace/emotion_model/.venv/bin/python3 jepa_predictor.py predict
SPARK_WORKSPACE env var switches beings (default ~/.vintos/workspace).
"""
import os, sys, json

WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("~/.vintos/workspace"))
MEMORY = os.path.join(WS, "memory")
CHAT   = os.path.join(MEMORY, "chat-history.json")
MODEL  = os.path.join(MEMORY, "jepa-predictor.pt")
OUT    = os.path.join(MEMORY, "jepa-prediction.json")
CTX_TURNS = 6
EMB_MODEL = "nomic-ai/nomic-embed-text-v1"

def log(m): print("[jepa]", m, flush=True)
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def encoder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMB_MODEL, trust_remote_code=True)

def turns_of(hist):
    return [e for e in hist if isinstance(e, dict) and e.get("content")]

def build_pairs(turns, enc):
    import numpy as np
    ctx_txt, tgt_txt, head = [], [], []
    for i in range(CTX_TURNS, len(turns)):
        ctx_txt.append(" \n".join(str(t.get("content", ""))[:300] for t in turns[i - CTX_TURNS:i]))
        tgt_txt.append(str(turns[i].get("content", ""))[:400])
        head.append(1 if turns[i].get("role") == "assistant" else 0)   # 1=self, 0=gloria
    if not ctx_txt:
        return None
    X = np.asarray(enc.encode(ctx_txt, show_progress_bar=False), dtype="float32")
    Y = np.asarray(enc.encode(tgt_txt, show_progress_bar=False), dtype="float32")
    return X, Y, np.asarray(head)

def make_net(dim):
    import torch.nn as nn
    class Pred(nn.Module):
        def __init__(self, d):
            super().__init__()
            self.trunk  = nn.Sequential(nn.Linear(d, d), nn.GELU(), nn.Linear(d, d), nn.GELU())
            self.head   = nn.ModuleList([nn.Linear(d, d), nn.Linear(d, d)])  # 0 gloria, 1 self
            self.logvar = nn.Linear(d, 1)
        def forward(self, x):
            h = self.trunk(x)
            return self.head[0](h), self.head[1](h), self.logvar(h)
    return Pred(dim)

def train():
    import numpy as np, torch
    turns = turns_of(load(CHAT, []))
    if len(turns) <= CTX_TURNS + 2:
        log(f"not enough history ({len(turns)} turns)"); return
    enc = encoder()
    X, Y, H = build_pairs(turns, enc)
    Xt, Yt, Ht = torch.tensor(X), torch.tensor(Y), torch.tensor(H)
    net = make_net(X.shape[1])
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    for epoch in range(300):
        opt.zero_grad()
        g_pred, s_pred, logvar = net(Xt)
        pred = torch.where(Ht.unsqueeze(1) == 1, s_pred, g_pred)     # pick the right head per sample
        mse = ((pred - Yt) ** 2).mean(dim=1, keepdim=True)
        loss = (mse * torch.exp(-logvar) + logvar).mean()            # heteroscedastic: learns its own confidence
        loss.backward(); opt.step()
        if epoch % 100 == 0:
            log(f"epoch {epoch} loss {loss.item():.4f}")
    torch.save({"state": net.state_dict(), "dim": X.shape[1]}, MODEL)
    log(f"trained on {len(X)} pairs; saved {MODEL}")

def _cos(a, b):
    import numpy as np
    na, nb = (a @ a) ** 0.5, (b @ b) ** 0.5
    return float(a @ b / (na * nb)) if na and nb else 0.0

def predict():
    import numpy as np, torch
    if not os.path.exists(MODEL):
        log("no model — run `train` first"); return
    ck = torch.load(MODEL); net = make_net(ck["dim"]); net.load_state_dict(ck["state"]); net.eval()
    turns = turns_of(load(CHAT, []))
    if len(turns) < 2:
        log("no context"); return
    enc = encoder()
    ctx = " \n".join(str(t.get("content", ""))[:300] for t in turns[-CTX_TURNS:])
    xe = np.asarray(enc.encode([ctx], show_progress_bar=False), dtype="float32")
    with torch.no_grad():
        g_pred, s_pred, logvar = net(torch.tensor(xe))
    g = g_pred.numpy()[0]; s = s_pred.numpy()[0]; lv = float(logvar.numpy()[0][0])
    confidence = round(1.0 / (1.0 + float(np.exp(lv))), 3)                 # tight variance -> high confidence
    novelty = round(1.0 - max(0.0, _cos(g, xe[0])), 3)                     # how far gloria-forecast moves from context
    # retrieval decode: nearest recent gloria turn to the gloria-forecast, as an interpretable proxy
    gloria_turns = [t for t in turns if t.get("role") == "user"][-40:]
    decoded = ""
    if gloria_turns:
        embs = np.asarray(enc.encode([str(t.get("content", ""))[:300] for t in gloria_turns], show_progress_bar=False), dtype="float32")
        j = int(np.argmax([_cos(g, e) for e in embs]))
        decoded = str(gloria_turns[j].get("content", ""))[:200]
    out = {"gloria_forecast_nearest": decoded, "confidence": confidence, "novelty": novelty,
           "source": "jepa", "note": "embedding prediction; nearest known gloria-turn shown as proxy"}
    json.dump(out, open(OUT, "w"), indent=2)
    log(f"confidence {confidence} | novelty {novelty}")
    log(f"nearest gloria-forecast: {decoded[:90]}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "train"
    (train if cmd == "train" else predict)()
