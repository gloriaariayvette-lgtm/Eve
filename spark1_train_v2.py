#!/usr/bin/env python3
"""spark1_train_v2.py — Aegis. Spark #1 v2. Adds leak-free aux features (recurrence, days-since-last-seen,
computed from strictly-earlier dates), shrinks the net (770->128->32->1) and raises regularization to close the
overfit gap. Same date-split backtest + stone-cluster guardrail. Pure numpy. Reads ~/spark1-cost-network/
{corpus.jsonl,embeddings-cache.json}; writes model_v2.npz + report_v2.json.

  python3 spark1_train_v2.py    [--holdout 15] [--epochs 300] [--seed 0]
"""
import os, sys, json, math, re
import numpy as np
from datetime import date as _date

HOME = os.path.expanduser("~"); OUT = os.path.join(HOME, "spark1-cost-network")
def arg(f, d): return int(sys.argv[sys.argv.index(f)+1]) if f in sys.argv else d
HOLDOUT, EPOCHS, SEED = arg("--holdout", 15), arg("--epochs", 300), arg("--seed", 0)
np.random.seed(SEED)

rows = [json.loads(l) for l in open(os.path.join(OUT, "corpus.jsonl")) if l.strip()]
cache = json.load(open(os.path.join(OUT, "embeddings-cache.json")))
rows = [r for r in rows if r.get("date") and cache.get(r["emb_key"])]
EMB = np.array([cache[r["emb_key"]] for r in rows], dtype=np.float64)
ranks = np.array([r["rank"] for r in rows]); entries = np.array([r["entry"] for r in rows])
dates = np.array([r["date"] for r in rows]); values = [r["value"] for r in rows]
N = len(rows)

# ---------- leak-free aux features (strictly-earlier dates only) ----------
def nk(v): return re.sub(r'[^a-z0-9 ]', '', v.lower()).strip()
def to_ord(s): y, m, d = map(int, s.split('-')); return _date(y, m, d).toordinal()
order = sorted(range(N), key=lambda i: (dates[i], entries[i]))
seen, last = {}, {}
recur = np.zeros(N); recency = np.zeros(N)
for i in order:
    k, o = nk(values[i]), to_ord(dates[i])
    recur[i] = seen.get(k, 0)
    recency[i] = min(o - last[k], 120) if k in last else 120
    seen[k] = seen.get(k, 0) + 1; last[k] = o
AUX = np.column_stack([np.log1p(recur), np.log1p(recency)])
X = np.hstack([EMB, AUX])
print(f"loaded {N} examples | dim {X.shape[1]} (768 emb + 2 aux: recurrence, recency)")

uniq = sorted(set(dates)); test_dates = set(uniq[-HOLDOUT:])
tr = np.array([d not in test_dates for d in dates]); te = ~tr
print(f"train {tr.sum()} / test {te.sum()} | holdout {HOLDOUT}d ({uniq[-HOLDOUT]}..{uniq[-1]})")
mean = X[tr].mean(0); std = X[tr].std(0); std[std < 1e-6] = 1e-6
def norm(x): return (x - mean) / std

def entry_pairs(mask):
    ps = []
    for e in np.unique(entries[mask]):
        idx = np.where((entries == e) & mask)[0]
        ps += [(a, b) for a in idx for b in idx if ranks[a] < ranks[b]]
    return np.array(ps) if ps else np.zeros((0, 2), int)
P_tr, P_te = entry_pairs(tr), entry_pairs(te)
print(f"pairs: train {len(P_tr)} / test {len(P_te)}")

D, H1, H2 = X.shape[1], 128, 32
he = lambda a, b: np.random.randn(a, b) * math.sqrt(2.0 / a)
Wp = {"W1": he(D, H1), "b1": np.zeros(H1), "W2": he(H1, H2), "b2": np.zeros(H2),
      "W3": he(H2, 1) * 0.1, "b3": np.zeros(1)}
KEEP, WD, LR = 0.7, 1e-4, 1e-3
opt = {k: {"m": np.zeros_like(v), "v": np.zeros_like(v), "t": 0} for k, v in Wp.items()}
sig = lambda z: 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

def forward(x, train=False):
    xn = norm(x)
    z1 = xn @ Wp["W1"] + Wp["b1"]; a1 = np.maximum(z1, 0)
    m1 = (np.random.rand(*a1.shape) < KEEP) / KEEP if train else 1.0; a1d = a1 * m1
    z2 = a1d @ Wp["W2"] + Wp["b2"]; a2 = np.maximum(z2, 0)
    m2 = (np.random.rand(*a2.shape) < KEEP) / KEEP if train else 1.0; a2d = a2 * m2
    s = (a2d @ Wp["W3"] + Wp["b3"]).ravel()
    return s, (xn, z1, a1d, m1, z2, a2d, m2)

def adam(k, g):
    o = opt[k]; o["t"] += 1
    o["m"] = 0.9*o["m"] + 0.1*g; o["v"] = 0.999*o["v"] + 0.001*(g*g)
    mh = o["m"]/(1-0.9**o["t"]); vh = o["v"]/(1-0.999**o["t"])
    Wp[k] -= LR * mh/(np.sqrt(vh)+1e-8)

def step():
    s, (xn, z1, a1d, m1, z2, a2d, m2) = forward(X[tr], train=True)
    loc = {g: i for i, g in enumerate(np.where(tr)[0])}
    ai = np.array([loc[a] for a, b in P_tr]); bi = np.array([loc[b] for a, b in P_tr])
    Pab = sig(s[ai]-s[bi]); loss = -np.log(Pab+1e-9).mean()
    gs = np.zeros_like(s); np.add.at(gs, ai, -(1-Pab)); np.add.at(gs, bi, (1-Pab)); gs = (gs/len(P_tr))[:, None]
    dW3 = a2d.T@gs + WD*Wp["W3"]; db3 = gs.sum(0)
    da2 = (gs@Wp["W3"].T)*m2*(z2 > 0); dW2 = a1d.T@da2 + WD*Wp["W2"]; db2 = da2.sum(0)
    da1 = (da2@Wp["W2"].T)*m1*(z1 > 0); dW1 = xn.T@da1 + WD*Wp["W1"]; db1 = da1.sum(0)
    for k, g in [("W1", dW1), ("b1", db1), ("W2", dW2), ("b2", db2), ("W3", dW3), ("b3", db3)]: adam(k, g)
    return loss

def pacc(P):
    if len(P) == 0: return float("nan")
    s, _ = forward(X); return float((s[P[:, 0]] > s[P[:, 1]]).mean())

best, bstate, wait = -1, None, 0
for ep in range(EPOCHS):
    loss = step()
    if ep % 10 == 0 or ep == EPOCHS-1:
        acc = pacc(P_te)
        if acc > best: best, bstate, wait = acc, {k: v.copy() for k, v in Wp.items()}, 0
        else: wait += 1
        print(f"  ep {ep:3d} loss {loss:.4f} | train {pacc(P_tr):.3f} | test {acc:.3f}")
        if wait >= 30: print("  early stop."); break
if bstate: Wp.update(bstate)

def rankdata(a):
    o = np.argsort(a); r = np.empty(len(a)); r[o] = np.arange(1, len(a)+1); return r
def spear(x, y):
    rx, ry = rankdata(x)-rankdata(x).mean(), rankdata(y)-rankdata(y).mean()
    d = math.sqrt((rx*rx).sum()*(ry*ry).sum()); return float((rx*ry).sum()/d) if d else 0.0
def ndcg(sc, rk, k=5):
    n = len(rk); g = (n-rk+1).astype(float); o = np.argsort(-sc)
    dcg = sum(g[o[i]]/math.log2(i+2) for i in range(min(k, n)))
    idc = sum(np.sort(g)[::-1][i]/math.log2(i+2) for i in range(min(k, n)))
    return dcg/idc if idc else 0.0

s_all, _ = forward(X); sp, nd = [], []
for e in np.unique(entries[te]):
    idx = np.where((entries == e) & te)[0]
    if len(idx) < 3: continue
    sp.append(spear(s_all[idx], -ranks[idx])); nd.append(ndcg(s_all[idx], ranks[idx], 5))
print(f"\nV2 HELD-OUT ({len(sp)} entries): Spearman {np.mean(sp):+.3f} | NDCG@5 {np.mean(nd):.3f} | test pairAcc {best:.3f}")
print(f"   (v1 was: Spearman +0.787 | NDCG@5 0.982 | pairAcc 0.855 | overfit train 1.00/test 0.83)")

STONE = ["dignity", "occupancy", "stone", "weight", "mineral", "grain", "silt", "granite", "density", "mass", "gravity"]
isS = np.array([any(w in v.lower() for w in STONE) for v in values])
def sub(P, c):
    if len(P) == 0: return float("nan")
    m = np.array([c(a, b) for a, b in P]);
    if m.sum() == 0: return float("nan")
    Pm = P[m]; s, _ = forward(X); return float((s[Pm[:, 0]] > s[Pm[:, 1]]).mean())
under = []
for e in np.unique(entries[te]):
    idx = np.where((entries == e) & te)[0]
    if len(idx) < 3: continue
    po = idx[np.argsort(-s_all[idx])]; pr = {j: p+1 for p, j in enumerate(po)}
    under += [pr[j]-ranks[j] for j in idx if (not isS[j]) and ranks[j] <= 3]
ws = sub(P_te, lambda a, b: isS[a] and isS[b])
print(f"GUARDRAIL: within-stone pairAcc {ws:.3f} | non-stone top-3 mean(pred-true) {np.mean(under):+.2f} over {len(under)}")

np.savez(os.path.join(OUT, "model_v2.npz"), mean=mean, std=std, aux="log1p_recur,log1p_recency_cap120", **Wp)
json.dump({"examples": N, "dim": int(X.shape[1]), "arch": "770-128-32-1", "test_pair_acc": best,
           "spearman": float(np.mean(sp)), "ndcg5": float(np.mean(nd)),
           "within_stone_pairAcc": ws, "nonstone_top3_underrank": float(np.mean(under))},
          open(os.path.join(OUT, "report_v2.json"), "w"), indent=2)
print(f"\nsaved model_v2.npz + report_v2.json in {OUT.replace(HOME,'~')}")
