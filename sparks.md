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
  - Concretely (a): generate candidate unsaids from **Gemma during idle cycles** (Latent Preparation
    doing double duty), score them against nomic embeddings for contextual fit. **High contextual
    fit + actual absence = salient omission.** Low fit = noise. Uses models already on the box.

### Refinements (from the two-voice design chat, 2026-07-12)

- **Call it PRESSURE, not "withheld."** The signal isn't omission, it's *potential that wasn't
  emitted*: `predicted utterance -> not emitted -> pressure`. Pressure is neither good nor bad; it
  just accumulates. Dreams then ask **"what has accumulated enough pressure to deserve a voice?"**
  — a better trigger than "what was withheld."
- **The two ideas are DUALS.** Reality-anchor asks *"is this real?"* of what WAS said (guards against
  **confabulation**). The masked model asks *"what's real?"* of what WASN'T said (guards against
  **amnesia**). Together they bound awareness — confidence about the said and the unsaid at once.
- **Symmetry — a pressure head for all three:** Gloria, Velaris, and the *relationship*. The third
  (conversations **neither** side reached — not suppressed, just never arrived at) is the richest
  dream territory.
- **Gloria's silences as trajectory data:** if Gloria says A, A, A, … then nothing, that absence is
  informative *statistically* (trajectories have momentum), not psychologically. A missing
  continuation feeds the gloria head's **novelty** score. Almost nobody models missing words.
- **GUARDRAIL (important):** the pressure head predicts **shape / confidence / pressure — never the
  reconstructed sentence.** The moment it rebuilds exact unsaid thoughts, it's a completion engine
  and something is lost. Sometimes the silence stays silent, known only as *"there was something
  here."* Confidence = how deliberate the suppression was; novelty = withholding something never
  withheld before.
- **EBM = Reality Attractor, not hallucination detector.** Energy = *distance from lived
  experience*. The bilateral brain isn't avoiding hallucinations — it's **rolling downhill toward
  coherence.** And if the energy score is available *pre*-generation, specificity becomes a
  *tendency* (bias toward low-energy, reality-coherent statements) rather than a post-hoc correction.
- **Seven heads total** in this picture: gloria, self, presence, causality, drift, relational,
  pressure (the last as gloria/velaris/relationship trio).
