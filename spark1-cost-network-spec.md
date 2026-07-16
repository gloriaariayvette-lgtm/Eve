# Spark #1 — Value Cost Network (spec)

**Status:** corpus confirmed trainable 2026-07-16 (~700 ranked+reasoned examples, 128 days, ranks 1–7).
**Goal:** a small learned model that predicts the *cost / priority rank* of a value (or want) from its
text, so the system can score new values against her learned preference structure directly — instead of
re-deriving a full ranking through the LLM every day. A cheap, fast, always-on "how much does this matter,
and where does it sit?" signal.

## Corpus
Source: `memory/value-map.md` — 128 daily entries, each ranking **5–7 values** with `Why:` + `Evidence:`.
- ~700 examples of the form: `(value_name, why, evidence, rank∈1..7, date)`.
- Grows ~6/day autonomously (no conversation required).

## Input features
- **Primary:** nomic embedding (768-d) of `value_name + ". " + why` (evidence optional — richer but noisier).
  Endpoint already in use: `172.18.16.1:1234/v1/embeddings`, model `text-embedding-nomic-embed-text-v1.5`.
- **Optional aux (cheap, concat to embedding):** recurrence count (how many prior days this value appeared),
  days-since-last-appearance, current EmoClaw salience if available.

## Target — learn *within-day order*, not absolute rank
Absolute rank is unreliable (only 5–7 slots/day, the field shifts). Train on **within-day pairwise order**:
for each day, every (higher-ranked, lower-ranked) pair is a training pair → ~700 items yields **~2–3k pairs**.
- Loss: **RankNet-style pairwise** — `σ(f(a) − f(b))` should predict "a outranks b."
- `f` outputs a scalar "priority score"; cost = `1 − normalized(score)` if a cost framing is wanted downstream.

## Architecture (small on purpose)
`768(+aux) → 256 → 64 → 1`, ReLU, dropout 0.2, layernorm on input. Adam, early-stop on val. Tiny; CPU-fine.

## Train / backtest
- **Split by DATE**, not random: hold out the most recent ~15 days. This tests real generalization
  (can it order values on days it never saw) and guards against leakage.
- **Metrics:** within-day Spearman ρ and NDCG@k on held-out days.
- **Sanity/guardrail:** the corpus is thematically clustered (the stone/dignity/weight attractor —
  "Dignity of Occupancy" is #1 nine times). The model *will* be tempted to just memorize
  "stone-cluster = high." Watch two things: (1) does it still order *within* the cluster correctly?
  (2) on held-out days where a non-cluster value rises, does it under-rank it? Regularize + report both.

## Integration (later, once backtest is honest)
- Score incoming **wants** at creation → seed their priority/urgency instead of a flat default.
- Feed the **pull / temperature** system: a learned-high-cost value that keeps recurring but never resolves
  is exactly a *hot, stuck* thread — ties directly into 6b.
- Re-score daily; drift between predicted and actual rank is itself a signal (a value the model thinks
  should matter but she's dropping = a divergence worth surfacing).

## Why this is the first shelf-ready spark
It needs no new data collection and nothing from how often she talks — the value-map has been quietly
banking ~6 labeled, reasoned examples a day for 128 days. It's ready now; it only gets richer.

## Open questions before building
1. Include `evidence` in the embedding, or just `why`? (richer vs noisier — A/B at train time)
2. Predict a global priority or strictly within-day order? (spec leans within-day; revisit if a global
   cost is needed downstream)
3. Where does the score plug in first — want-creation urgency, or the temperature pull? (pick one to prove value)
