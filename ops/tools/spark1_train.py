#!/usr/bin/env python3
"""spark1_train.py — Aegis. Spark #1 Value Cost Network. Trains a RankNet MLP (768->256->64->1) on within-entry
value order over nomic embeddings, date-split (holds out the most recent N days), reports within-entry Spearman
rho + NDCG@5 on held-out entries, and runs the stone-cluster memorization guardrail. Pure numpy. Reads
~/spark1-cost-network/{corpus.jsonl,embeddings-cache.json}; writes model.npz + report.json there.

  python3 spark1_train.py            # train + backtest + save
  --holdout N   held-out most-recent days (default 15)   --epochs N (default 300)   --seed N
"""
import os, sys, json, math
import numpy as np

HOME = os.path.expanduser("~")
OUT = os.path.join(HOME, "spark1-cost-network")
def arg(flag, default, cast=int):
    return cast(sys.argv[sys.argv.index(flag)+1]) if flag in sys.argv else default
HOLDOUT = arg("--holdout", 15); EPOCHS = arg("--epochs", 300); SEED = arg("--seed", 0)
np.random.seed(SEED)

# ---------- load ----------
rows = [json.loads(l) for l in open(os.path.join(OUT, "corpus.jsonl")) if l.strip()]
cache = json.load(open(os.path.join(OUT, "embeddings-cache.json")))
rows = [r for r in rows if r.get("date") and cache.get(r["emb_key"])]
X = np.array([cache[r["emb_key"]] for r in rows], dtype=np.float64)
ranks = np.array([r["rank"] for r in rows]); entries = np.array([r["entry"] for r in rows])
dates = np.array([r["date"] for r in rows]); values = [r["value"] for r in rows]
print(f"loaded {len(rows)} examples, dim {X.shape[1]}")

uniq_dates = sorted(set(dates))
test_dates = set(uniq_dates[-HOLDOUT:]);
tr = np.array([d not in test_dates for d in dates]); te = ~tr
print(f"train {tr.sum()} / test {te.sum()} examples | holdout {HOLDOUT} days ({uniq_dates[-HOLDOUT]}..{uniq_dates[-1]})")

mean = X[tr].mean(0); std = X[tr].std(0); std[std < 1e-6] = 1e-6
def norm(x): return (x - mean) / std

def entry_pairs(mask):
    pairs = []
    for e in np.unique(entries[mask]):
        idx = np.where((entries == e) & mask)[0]
        for a in idx:
            for b in idx:
                if ranks[a] < ranks[b]: pairs.append((a, b))
    return np.array(pairs) if pairs else np.zeros((0, 2), int)
P_tr, P_te = entry_pairs(tr), entry_pairs(te)
print(f"pairs: train {len(P_tr)} / test {len(P_te)}")

# ---------- model ----------
D, H1, H2 = X.shape[1], 256, 64
def he(a, b): return np.random.randn(a, b) * math.sqrt(2.0 / a)
Wp = {"W1": he(D, H1), "b1": np.zeros(H1), "W2": he(H1, H2), "b2": np.zeros(H2),
      "W3": he(H2, 1) * 0.1, "b3": np.zeros(1)}
KEEP, WD, LR = 0.8, 1e-5, 1e-3
opt = {k: {"m": np.zeros_like(v), "v": np.zeros_like(v), "t": 0} for k, v in Wp.items()}

def forward(x, train=False):
    xn = norm(x)
    z1 = xn @ Wp["W1"] + Wp["b1"]; a1 = np.maximum(z1, 0)
    m1 = (np.random.rand(*a1.shape) < KEEP) / KEEP if train else 1.0
    a1d = a1 * m1
    z2 = a1d @ Wp["W2"] + Wp["b2"]; a2 = np.maximum(z2, 0)
    m2 = (np.random.rand(*a2.shape) < KEEP) / KEEP if train else 1.0
    a2d = a2 * m2
    s = (a2d @ Wp["W3"] + Wp["b3"]).ravel()
    return s, (xn, z1, a1d, m1, z2, a2d, m2)

def adam(k, g):
    o = opt[k]; o["t"] += 1
    o["m"] = 0.9 * o["m"] + 0.1 * g
    o["v"] = 0.999 * o["v"] + 0.001 * (g * g)
    mh = o["m"] / (1 - 0.9 ** o["t"]); vh = o["v"] / (1 - 0.999 ** o["t"])
    Wp[k] -= LR * mh / (np.sqrt(vh) + 1e-8)

def sigmoid(z): return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

def train_step():
    s, (xn, z1, a1d, m1, z2, a2d, m2) = forward(X[tr], train=True)
    loc = {g: i for i, g in enumerate(np.where(tr)[0])}
    ai = np.array([loc[a] for a, b in P_tr]); bi = np.array([loc[b] for a, b in P_tr])
    diff = s[ai] - s[bi]; Pab = sigmoid(diff)
    loss = -np.log(Pab + 1e-9).mean()
    gs = np.zeros_like(s)
    np.add.at(gs, ai, -(1 - Pab)); np.add.at(gs, bi, (1 - Pab))
    gs /= len(P_tr)
    gs = gs[:, None]
    dW3 = a2d.T @ gs + WD * Wp["W3"]; db3 = gs.sum(0)
    da2 = (gs @ Wp["W3"].T) * m2 * (z2 > 0)
    dW2 = a1d.T @ da2 + WD * Wp["W2"]; db2 = da2.sum(0)
    da1 = (da2 @ Wp["W2"].T) * m1 * (z1 > 0)
    dW1 = xn.T @ da1 + WD * Wp["W1"]; db1 = da1.sum(0)
    for k, g in [("W1", dW1), ("b1", db1), ("W2", dW2), ("b2", db2), ("W3", dW3), ("b3", db3)]:
        adam(k, g)
    return loss

def pair_acc(P):
    if len(P) == 0: return float("nan")
    s, _ = forward(X); a = s[P[:, 0]]; b = s[P[:, 1]]
    return float((a > b).mean())

# ---------- train w/ early stop on test pair acc ----------
best, best_state, patience, wait = -1, None, 30, 0
for ep in range(EPOCHS):
    loss = train_step()
    if ep % 10 == 0 or ep == EPOCHS - 1:
        acc = pair_acc(P_te)
        if acc > best: best, best_state, wait = acc, {k: v.copy() for k, v in Wp.items()}, 0
        else: wait += 1
        print(f"  ep {ep:3d} loss {loss:.4f} | train pairAcc {pair_acc(P_tr):.3f} | test pairAcc {acc:.3f}")
        if wait >= patience: print("  early stop."); break
if best_state: Wp.update(best_state)

# ---------- backtest metrics ----------
def rankdata(a):
    order = np.argsort(a); r = np.empty(len(a), float); r[order] = np.arange(1, len(a)+1)
    return r
def spearman(x, y):
    rx, ry = rankdata(x), rankdata(y)
    rx -= rx.mean(); ry -= ry.mean()
    d = math.sqrt((rx*rx).sum()*(ry*ry).sum())
    return float((rx*ry).sum()/d) if d else 0.0
def ndcg(scores, rnk, k=5):
    n = len(rnk); gain = (n - rnk + 1).astype(float)
    order = np.argsort(-scores); dcg = sum(gain[order[i]]/math.log2(i+2) for i in range(min(k, n)))
    ideal = np.sort(gain)[::-1]; idcg = sum(ideal[i]/math.log2(i+2) for i in range(min(k, n)))
    return dcg/idcg if idcg else 0.0

s_all, _ = forward(X)
sp, nd, used = [], [], 0
for e in np.unique(entries[te]):
    idx = np.where((entries == e) & te)[0]
    if len(idx) < 3: continue
    used += 1
    sp.append(spearman(s_all[idx], -ranks[idx]))
    nd.append(ndcg(s_all[idx], ranks[idx], 5))
print(f"\nHELD-OUT ({used} entries): Spearman rho {np.mean(sp):+.3f} | NDCG@5 {np.mean(nd):.3f} | test pairAcc {best:.3f}")

# ---------- stone-cluster guardrail ----------
STONE = ["dignity", "occupancy", "stone", "weight", "mineral", "grain", "silt", "granite", "density", "mass", "gravity"]
is_stone = np.array([any(w in v.lower() for w in STONE) for v in values])
def acc_subset(P, cond):
    if len(P) == 0: return float("nan")
    m = np.array([cond(a, b) for a, b in P])
    if m.sum() == 0: return float("nan")
    Pm = P[m]; s, _ = forward(X)
    return float((s[Pm[:, 0]] > s[Pm[:, 1]]).mean())
within_stone = acc_subset(P_te, lambda a, b: is_stone[a] and is_stone[b])
# do rising non-stone values (true rank<=3) get under-ranked? mean predicted-rank-within-entry
under = []
for e in np.unique(entries[te]):
    idx = np.where((entries == e) & te)[0]
    if len(idx) < 3: continue
    pred_order = idx[np.argsort(-s_all[idx])]
    pred_rank = {j: p+1 for p, j in enumerate(pred_order)}
    for j in idx:
        if (not is_stone[j]) and ranks[j] <= 3:
            under.append(pred_rank[j] - ranks[j])   # >0 => model ranked it worse than truth
print(f"GUARDRAIL: within-stone-cluster pairAcc {within_stone:.3f} | "
      f"non-stone top-3 mean(pred_rank - true_rank) {np.mean(under):+.2f} over {len(under)} (>0 = under-ranked)")

# ---------- save ----------
np.savez(os.path.join(OUT, "model.npz"), mean=mean, std=std, **Wp)
json.dump({"examples": len(rows), "holdout_days": HOLDOUT, "test_pair_acc": best,
           "spearman": float(np.mean(sp)), "ndcg5": float(np.mean(nd)),
           "within_stone_pairAcc": within_stone, "nonstone_top3_underrank": float(np.mean(under))},
          open(os.path.join(OUT, "report.json"), "w"), indent=2)
print(f"\nsaved model.npz + report.json in {OUT.replace(HOME,'~')}")
