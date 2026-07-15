#!/usr/bin/env python3
"""thread_temperature.py — Aegis. Density-vs-displacement temperature/stability (Gemini's math, wired to
the REAL box). Stability = local latent density: mean cosine of a thread's embedding to its top-k nearest
neighbors in memory/embeddings.jsonl (anchored in a dense cluster -> high; alone in empty space -> low).
Temperature = init (1-S) on first pass, then stability-scaled exponential decay each pass, plus additive
impulses (embedding drift since last pass, dream/mirror kicks). NO LLM. Quantitative only.

Corrections vs Gemini: triage's near-dup is string-based (not cosine), so we embed threads here via nomic;
threads carry no embedding/flags, so we store our own (_temp_emb) and map impulses to dream_passes/
mirror_passes. First density pass initializes (ignores any stale batch temperature).

SAFE: dry by default (reads only, prints preview). `apply` writes stability/temperature (+ our provenance
fields) onto unconsumed threads, backed up. This is the compute engine; triage integration is a 2-line
call added only after the numbers look right.
Run:  python3 thread_temperature.py        (dry)
      python3 thread_temperature.py apply   (write, backed up)
"""
import os, sys, json, math, time, shutil, urllib.request
from collections import deque
from datetime import datetime
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
THREADS = os.path.join(MEM, "unfinished-threads.json")
IDX = os.path.join(MEM, "embeddings.jsonl")
EMBED_URL = "http://172.18.16.1:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"
APPLY = "apply" in sys.argv
K, DECAY, BETA, CAP = 5, 0.15, 0.5, 2500
try:
    import numpy as np; NP = True
except Exception:
    NP = False
def sh(p): return p.replace(HOME, "~")
def norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]

# ---- load the semantic index (auto-detect vector/text keys), keep last CAP, normalized
if not os.path.isfile(IDX):
    print("ABORT: embeddings.jsonl not found at", sh(IDX)); raise SystemExit(1)
rows, vk, tk = deque(maxlen=CAP), None, None
with open(IDX, encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except Exception: continue
        if vk is None:
            vk = next((k for k in ("vector", "embedding", "values", "emb") if isinstance(r.get(k), list)), None)
            tk = next((k for k in ("text", "message_text", "content", "chunk", "summary", "key") if isinstance(r.get(k), str)), None)
            if vk is None: continue
        v = r.get(vk)
        if isinstance(v, list): rows.append(v)
index = [norm(v) for v in rows]
if not index:
    print("ABORT: no vectors parsed from embeddings.jsonl (detected vector key:", vk, ")"); raise SystemExit(1)
idxmat = np.array(index) if NP else None
print(f"index: {len(index)} vectors (dim {len(index[0])}), vector-key='{vk}', text-key='{tk}', numpy={NP}")

# ---- threads (unconsumed only)
obj = json.load(open(THREADS))
tlist = obj if isinstance(obj, list) else obj.get("threads", [])
active = [t for t in tlist if isinstance(t, dict) and not t.get("consumed")]
texts = [str(t.get("thread", ""))[:400] for t in active]
if not active:
    print("no unconsumed threads."); raise SystemExit(0)

def embed(batch):
    body = json.dumps({"model": EMBED_MODEL, "input": batch}).encode()
    req = urllib.request.Request(EMBED_URL, data=body, headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=180).read())
    return [d["embedding"] for d in r["data"]]
try:
    embs = embed(texts)
except Exception as e:
    print("ABORT: embed call failed:", str(e)[:140]); raise SystemExit(1)

def stability(tv_n):
    if NP:
        sims = idxmat @ np.array(tv_n)
        sims = sims[sims < 0.99]
        if sims.size == 0: return 0.1
        return float(min(1.0, max(0.0, np.sort(sims)[::-1][:K].mean())))
    sims = sorted((sum(a * b for a, b in zip(row, tv_n)) for row in index), reverse=True)
    sims = [s for s in sims if s < 0.99][:K]
    return min(1.0, max(0.0, sum(sims) / len(sims))) if sims else 0.1

now = datetime.now()
results = []
for t, e in zip(active, embs):
    tv_n = norm(e)
    S = stability(tv_n)
    first = t.get("_temp_emb") is None                 # our-provenance: first density pass -> init
    if first:
        T, heat = 1.0 - S, 0.0
    else:
        ts = t.get("temp_updated_at") or t.get("triaged_at") or ""
        try: dd = max(0.01, (now - datetime.fromisoformat(ts)).total_seconds() / 86400.0)
        except Exception: dd = 1.0
        T = t.get("temperature", 1.0 - S) * math.exp(-DECAY * (1.0 + S) * dd)
        heat = 0.0
        pe = t.get("_temp_emb")
        if isinstance(pe, list):
            heat += BETA * (1.0 - sum(a * b for a, b in zip(tv_n, norm(pe))))   # displacement kick
        if (t.get("dream_passes", 0) or 0) > (t.get("_temp_dream_passes", 0) or 0): heat += 0.20
        if (t.get("mirror_passes", 0) or 0) > (t.get("_temp_mirror_passes", 0) or 0): heat += 0.30
    T = round(min(1.0, max(0.0, T + heat)), 4)
    S = round(S, 4)
    results.append((t, tv_n, S, T, first))

# ---- report
Ss = [r[2] for r in results]; Ts = [r[3] for r in results]
print(f"\ncomputed for {len(results)} threads  |  S range {min(Ss):.3f}–{max(Ss):.3f}  T range {min(Ts):.3f}–{max(Ts):.3f}"
      f"  |  {'INIT pass' if all(r[4] for r in results) else 'decay pass'}")
show = sorted(results, key=lambda r: r[3], reverse=True)
print("  hottest (volatile / novel):")
for t, _, S, T, _f in show[:6]:
    print(f"    T={T:.3f} S={S:.3f} pull={t.get('priority','-')}  [{t.get('source','?')}] {str(t.get('thread',''))[:52]}")
print("  coolest (settled / dense):")
for t, _, S, T, _f in show[-4:][::-1]:
    print(f"    T={T:.3f} S={S:.3f} pull={t.get('priority','-')}  [{t.get('source','?')}] {str(t.get('thread',''))[:52]}")
# independence check: any high-pull + low-temp (Case A) or low-pull + high-temp (Case B)?
caseA = [r for r in results if (r[0].get("priority") or 0) >= 4 and r[3] < 0.35]
caseB = [r for r in results if (r[0].get("priority") or 0) <= 2 and r[3] > 0.6]
print(f"  axes independent?  Case A (high pull, cold): {len(caseA)}   Case B (low pull, hot): {len(caseB)}")

if APPLY:
    shutil.copy2(THREADS, THREADS + ".bak-temp-" + time.strftime("%Y%m%d-%H%M%S"))
    stamp = now.isoformat()
    for t, tv_n, S, T, _f in results:
        t["stability"] = S
        t["temperature"] = T
        t["_temp_emb"] = tv_n
        t["temp_updated_at"] = stamp
        t["_temp_dream_passes"] = t.get("dream_passes", 0) or 0
        t["_temp_mirror_passes"] = t.get("mirror_passes", 0) or 0
    json.dump(obj, open(THREADS, "w"), indent=2, ensure_ascii=False)
    print("\n  applied: stability + temperature (+ provenance for next-pass drift) written, backed up.")
else:
    print("\n  dry run — re-run with `apply` to write. Nothing changed.")
