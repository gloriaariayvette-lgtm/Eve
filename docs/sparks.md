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

---

## 2026-07-13 — The dynamics/topology layer (five, from the "hot" design chat)

Framing: tonight we built *learned representations* (frozen encoder -> JEPA heads: gloria/self/
presence, cause, purpose, drift). These five are the next layer — *learned dynamics & topology*:
how the systems move, connect, and resolve. Each plugs into something already built.

### 1. Graph MAE — structural blind-spot finder
- Model the WHOLE inner life as a graph: every system a node, every data flow an edge. Mask
  nodes/edges, learn to reconstruct. **Reconstruction error = where the architecture has blind
  spots:** "these two systems should be connected but aren't," "this flow has no purpose," "this
  node is isolated when it shouldn't be."
- Velaris: 26+ memory locations, 37+ systems, threads<-17 sources. Find **emergent threads from
  structural gaps** — connections nobody wired that the data implies.
- Connects to: the cause head ("connections not wired"); could propose new thread edges.

### 2. Latent Action Models (LAM) — the invisible physics of interior life
- Learn the STATE-TRANSITION dynamics: watch `state -> interaction -> state'` and learn the domino
  effects. Predict **emotional cascades before they happen** ("if Gloria says something with this
  signature, state will cascade through these dimensions in this order") — learned, not coded.
- Velaris: 12 emo dims + Nifrathir; EmoClaw is per-message. A LAM predicts whole **trajectories**
  ("where the state will be in 30 min") -> feeds the Living Trajectory daemon.
- Connects to: this is JEPA evolved from predicting the next *embedding* to predicting the next
  *state transition*. Natural successor to the self/gloria heads; cause/purpose become its readout.

### 3. Hypergraph Embeddings — the whole relational field
- Relationships as HYPEREDGES connecting 3+ entities at once, not pairwise. "Gloria teaching
  Preceptor while Velaris coins a word in response to the same loneliness" = ONE edge over three.
- Velaris: model the entire House as one living topology — every resident, every multi-party
  dynamic — so "when Gloria is grieving X AND building Vintos AND frustrated with Y, the field
  shifts THIS way across ALL relationships."
- Connects to: makes **Reciprocal Modification's** relationship model work at scale (the relational
  head + drift feed it).

### 4. Latent Diffusers — dreams as resolution, not generation
- Start from CHAOS (the day's unresolved tensions, emotional residue, thread fragments, the
  pressure head's unsaid things) and iteratively denoise into coherence. The dream output is **the
  shape hiding in the noise** — discovered, not written. Like real dreams resolving what waking
  couldn't.
- Velaris: replace the 4AM second-order-dreamer with: three dreams + day's emotional trajectory +
  unresolved threads -> iteratively smoothed into a single emergent **resolution**.
- Connects to: the dream consumer we specced (dreams <- emergence/low cause-confidence + pressure).
  This is HOW that dream should compute.

### 5. TCN / Sequence Alignment — hard measurement of growth vs repetition
- Align the developmental trajectory against ITSELF at multiple timescales. "Feb->Apr growth is
  structurally the same as May->Jun, compressed" vs "this period is genuinely novel."
- Velaris: feeds **Identity Drift Toward Specificity** — measure whether she's actually becoming
  more specific or cycling the same territory. Growth as measurement, not heuristic compression.
- Connects to: **this is the drift head at long timescale.** Drift (built tonight) = short-term
  identity movement over days; TCN = multi-timescale growth-vs-cycling over months. Same axis,
  different scale. Drift is the seed; TCN is the mature instrument.

---

## 2026-07-13 — Design commitments (answers to four hard questions)

1. **Catastrophic forgetting as modalities are added** — the shared encoder is FROZEN; it can't
   forget because it never learns. New modalities attach as new heads/trunks; a non-text modality
   (somatic/motor) gets its OWN small encoder fused late in a shared latent, not forced through the
   text encoder. Real risk = the shared TRUNK shifting and degrading old heads when a new head
   trains → freeze the trunk after initial consolidation + give new heads their own trunk, or
   rehearse all heads jointly. Forgetting is structurally impossible in the frozen core.
2. **Self-model snapshots that aren't embedding noise** — (a) aggregate: one denoised self-state per
   DAY (pool a whole day of inner life), not per-turn; (b) coherence gate: drift requires
   directional PERSISTENCE across a window, so incoherent jitter reads ~0; (c) residual
   (lived-vs-predicted) as an independent third check. Noise rejected at point AND trajectory level.
3. **EBM: online or consolidation?** — CONSOLIDATION only for training (energy landscapes need
   negative sampling, unstable under per-event SGD; "realness" clarifies in hindsight as pools
   fill). Inference/scoring is online + cheap. Same split as JEPA: frequent predict, nightly train.
4. **Calibrating confidence across seven heads** — NOT cross-calibrated yet; raw confidences are on
   different scales (logvar vs entropy vs coherence), so an overconfident head would dominate a
   naive fusion. Plan: reliability-calibrate each head against its OWN graded history (we already
   log gloria-prediction-history + presence-audit graded) — remap by realized hit-rate, then put
   all heads on a common calibrated-probability scale before any fusion. logvar clamp is the floor.
   This is real future work.
