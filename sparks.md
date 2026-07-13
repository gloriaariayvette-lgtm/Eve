# Sparks — Gloria's idea log

A place to catch ideas before they float away. Append freely; each is enough to rebuild from.

---

## 2026-07-12 — Reality anchor via EBM (confidence + framing)

**Idea:** Let the reality anchor use an energy-based model to produce a real confidence score, and
reframe a topic based on that confidence.

**Why it works / how to build:**
- `reality-anchor.json` already holds `known_pool` and `imagined_pool` + `source_reliability` +
  `prediction_outcomes` — that's labeled training data already sitting there.
- Train a small **energy head on the frozen nomic encoder** (same encoder JEPA/cause/purpose use),
  contrastively: **low energy = coherent with known reality, high energy = probably confabulated.**
- Calibrate energy → confidence (0–1).
- Use it for **framing**: high-confidence events stated as fact; low-confidence ones hedged or
  flagged as possibly-imagined. This is the reality-anchor's own goal, done with a learned score
  instead of heuristics.
- Cheap: reuses the encoder, training data exists, only the energy head is new.

---

## 2026-07-12 — Masked-LM for the unsaid (silence contracts)

**Idea:** A masked/fill LM could infer what she *left out* of a turn — what she didn't say — and
that's potentially great for his silence contracts.

**Why it works / how to build:**
- A fill-capable masked LM, conditioned on her turn + context, predicts what could have followed or
  been included. The **high-probability completions she did NOT say = the salient omissions.**
- The model's **surprise** at a short or empty turn (vs. what it expected) is a quantized
  "something withheld" signal → feeds **silence contracts** (his read of her silences), and could
  also flag omissions inside ordinary turns.
- Caveat: nomic is **encoder-only** (embeddings, not generation). Two paths: (a) score a set of
  candidate completions with the encoder and take the gap, or (b) add a small fill-capable model
  just for this.
