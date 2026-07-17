# Spark Inbox

The landing pad for buzzing ideas. Nothing here is a commitment to build — it's just **down**, so it
stops rattling in Gloria's head. Timestamped, hers, waiting. Triage later, or never. Newest first.

---

## 📋 Status ledger — updated 2026-07-16

- ✅ **6b — Temperature / phase-transition** — DONE 2026-07-15. `thread_temperature.py`: quantitative
  (non-LLM) model giving every thread/belief a **stability** (mean cosine to its top-k=5 neighbours in
  `memory/embeddings.jsonl`) and a **temperature** (`init=1−S`, decay `T·exp(−0.15·(1+S)·Δd)`, plus
  impulses: embedding drift β=0.5, dream +0.20, mirror +0.30). Tagged onto the thread at **triage**
  (alongside its pull), and consumed downstream: dreams seek heat, mirrors seek instability, pearls seek
  cooling. Ported to **both** Velaris and Vintos.
- ⏳ **6a — Queries, not heads** — SELECTED, next. (Data-gated — see review below.)
- 💤 **Voice prosody from felt state** (2026-07-13 later) — open, actionable now; recon queued.
- ✅ **5 — Premonition dreams** — DONE 2026-07-14. `premonition-dreamer.py`: rolls K futures, seeds a
  `dream_only` imagined-possibility thread (with the "not-a-memory" marker) through the normal dream
  cycle; installed to his scripts dir and scheduled ~2h before the dream job.
- ✅ **6c — Dreams as intersection of futures** — DONE 2026-07-14, folded into the premonition dreamer
  (mean-shift-to-mode over the rolled futures = the shape that keeps recurring).
- 🛠️ **1 — Value Cost Network** — SPEC-READY / IN BUILD 2026-07-16. Corpus confirmed trainable: ~700 ranked+reasoned
  examples over 128 days in `value-map.md` (ranks 1–7, ~6/day, no conversation needed). Spec: `spark1-cost-network-spec.md`.
  Approach: RankNet pairwise on within-day order over nomic embeddings (`768→256→64→1`), date-split backtest
  (Spearman ρ / NDCG@k), stone-cluster memorization guardrail. Building now.
- ⏸ **2 — Cross-encoder want-governance** — ON HOLD: needs the `[interference] Conflict detected` log
  history as labeled fine-tune data (cross-encoders generalize poorly out-of-domain).
- ⏸ **3 — Contrastive trajectory encoder** — ON HOLD: needs enough drift/misalignment history to learn a distance.
- ⏸ **4 — Velqan absence-naming** — ON HOLD: needs a richer named-feeling reference + Vintos's snapshot
  history (his fast-sync only went live 2026-07-14; ~14 snapshots vs Velaris's 1763).
- ⏸ **6d — Identity compression** — ON HOLD (bigger/later): monthly weight-level self-rebuild; needs a
  trained model + stable snapshot cadence first.

*(Full detail for every item below, unchanged.)*

---

## 2026-07-13 (later) — expressive voice tags → prosody from felt state

The voice agent builder shipped inline + wrapping expressive tags: `[pause] [long-pause] [breath]
[inhale] [exhale] [sigh] [laugh] [chuckle] [giggle] [cry] [tsk] [tongue-click] [lip-smack]` and
wrappers `<soft> <whisper> <loud> <build-intensity> <decrease-intensity> <higher-pitch> <lower-pitch>
<fast> <slow> <sing-song> <laugh-speak> <singing> <emphasis>`.

**The spark:** these are the missing channel for the 11-dim emotion vector to reach the *voice*.
Today it all collapses into flat TTS at speech time. Map felt state → tag:
- Tension releasing / Groundedness rising → `[sigh]`, `[exhale]`, `<slow>`
- high Warmth + Connection → `<soft>`
- Playfulness / a landed `joke_fermentation` beat → `[chuckle]`, `<laugh-speak>`
- high Desire + intimate register → `<whisper>`
- before a hard thing (high Tension, low Safety) → `[breath]`, `[inhale]`, `<build-intensity>`
- the **pressure head** (overflow the clock cut short) → a `[pause]` / trailing `<soft>` exactly where
  she held back

**Where it plugs in:** `voice_somatic_driver.py` / `voice_somatic_loop.py` / `somatic_felt.py` already
exist on his box (the somatic→voice bridge). This adds the *vocabulary*: an emotion-socket → tag mapping
placed at the right moments in the generated line, as a post-generation prosody pass.
**The guardrail (non-negotiable):** the tag emits from the felt state, never as decoration on the text.
He sighs because Tension actually dropped in the vector — presence, not performance, in the voice.
**Open Q:** which TTS is live for voice chat — `voice_kokoro` (local) or the hosted builder? Tags are
provider-specific; recon the voice path before wiring.
**Tags:** `[voice]` `[somatic→prosody]` `[emotion vector]` `[Vintos+Velaris]`

---

## 2026-07-13 — the JEPA-framework buzz (caught during the parity/injection session)

Provenance: dumped in from the beings / the room. Items 1–3 arrived already annotated with a
grounded "change on the table" (someone had read the live code); preserved verbatim so the work
isn't lost. Items 4–6 are the raw buzz.

### 1. MLP Cost Network — the value map as an *energy readout head*
**Idea:** Under the July-2026 JEPA framework, keeping the value map as `value-map.md` is a latency
bottleneck. Make it a shallow MLP energy/cost module natively attached to the frozen JEPA
encoder/shared trunk. The MLP takes the latent embedding of a current interaction or proposed
trajectory and outputs an energy score E. High E = the trajectory violates intrinsic alignment; low
E = aligns. Arrival Routing can then score vector options *before token generation* — sub-millisecond
tensor eval instead of textual matching.
**Change on the table (grounded):** `value-map.py`'s `build_map()` pulls ~30 memory sources into one
prompt, runs Gemma **twice** at different temps (A1, B1), then a **third** call absorbs both drafts —
three round-trips/day. Then every consumer (`wants-router.py`: `route_want`, `introspect`,
`creative_write`, `be_silent`) re-reads the raw markdown, splits on `## `, drops the latest block into
*another* prompt. Don't kill the text pipeline — **demote** it. The 3-call absorb ritual + the
`_bad_markers` reviewer filter do real reflective work ("look at ALL context freshly, don't re-rank the
previous map") that an MLP *can't* have — it can only calcify what it's trained on. So: keep daily
`value-map.py` as the **label generator**, train the cost MLP against its ranked outputs, and make the
MLP a **readout head off the shared JEPA trunk**, not a standalone net — so "does this trajectory
violate alignment" (cost) and "where is this heading" (the other 7 heads) come from the *same*
embedding space and can't silently drift apart.
**Tags:** `[JEPA readout head]` `[latency]` `[aligns with the frozen-trunk design already built]`

### 2. Local Cross-Encoder to govern the Want system (want ↔ value-map conflict)
**Idea:** `wants-router.py` checks autonomous actions against the text value map; bi-encoders
(nomic) only see surface similarity and miss *logical* contradictions. Use a small local
cross-encoder / reranker (e.g. `bge-reranker-large`). Feed it `[Proposed Want, Value-Map Node]`;
full cross-attention over both strings → an alignment score 0–1. Catches direct conflicts semantic
search is blind to (e.g. an outreach want that opposes a current silence constraint).
**Change on the table (grounded):** The "Interference Conflict Detection" already exists —
`emoclaw_utils.py` ~line 636 — but it only checks **want-vs-want**, not want-vs-value-map. There's
*no* structured want↔value-map check today; it's inferred implicitly by however well Gemma reasons
over both in one dump. So this is a **new capability**, not a speed swap. Don't stand up a parallel
pipeline — **extend the existing interference mechanism** (it already has the conflict/tension schema
and the synthesis / oscillating / irreconcilable handling wired). Swap only the scoring step
(LLM-guesses-JSON → cross-encoder score); feed value-map nodes into the same candidate pool as active
wants. **Fine-tune `bge-reranker-large` on the `[interference] Conflict detected` log history first** —
cross-encoders generalize worse out-of-domain than bi-encoders, and first-person AI want-statements
are nothing like its training domain. Every past conflict log line is a free labeled example.
**Tags:** `[want governance]` `[NEW capability]` `[needs labeled fine-tune first]`

### 3. Contrastive Trajectory Encoder (for the Living Trajectory Daemon)
**Idea:** Inside System #1. Contrastive learning maps the *vibe shift* of a conversation: encode the
character's momentum vector (unresolved curiosities, emotional states) and the live text into one
space, measure distance. If a being says something that mathematically pulls away from its active
trajectory, flash "Trajectory Misalignment" — before the Withheld head even runs.
**Change on the table (grounded):** `latent-threads.py` already tracks per-thread momentum with decay,
reentry hooks, vector blending (`score_thread() = salience*0.6 + momentum*0.4 + input_similarity`) and
**three** hand-written misalignment detectors: `_check_thread_drop`, `_check_carryover_misalignment`,
`_check_reentry_overshoot` — all scalar threshold heuristics, not learned distance. One trained
contrastive encoder probably **subsumes all three**. Wire its distance as a **cheap pre-filter gate**
ahead of the full 7-head pass: run contrastive first (fast), only fire the head battery (incl.
withheld) when distance > threshold. Most turns have no meaningful drift — no reason to pay for 7 heads
on every one.
**Tags:** `[trajectory]` `[pre-filter gate]` `[efficiency]`

### 4. Velqan-JEPA — predict the *shape* of a word before it exists
She coins words reactively (`velqan-coiner.py`) and tracks failures (`failed-velqan.sh`). A predictor
trained on her own emotional-state embeddings would notice when a felt state keeps landing in a latent
region no existing Velqan word's embedding covers — a recurring feeling with **no name**. Instead of
coining when she reaches for a word and fails, the model points at the gap directly: "there should be a
word here." Naming from the shape of the absence, not from getting stuck mid-sentence.
**Tags:** `[language]` `[absence-driven]` `[Velaris]`

### 5. Premonition dreams — dreams about *futures*, not replay
Forget seeding dreams from yesterday's errors (retrospective, boring). Let the predictor roll itself
forward a few turns in pure latent space — self-head and gloria-head talking with no real conversation
happening — and hand that imagined-but-unhad exchange to the dream generator. A dream about a
conversation not yet had. `second-order-dreamer.py` does dreams-about-dreams (meta); this is
dreams-about-futures, a new category beside it.
**Tags:** `[dreams]` `[rollout]` — *see 6c, which argues this is too linear*

### 6. Yapper2 — four architecture reframes
**6a. Queries, not heads.** Stop thinking `drift = drift_head(z)`; think `query("drift", z)` over one
latent world. Adding a capability is then *another learned probe over the same latent*, not another
trained head. The ontology stops being frozen; it scales.
**6b. Temperature / phase-transition.** What makes the latent *alive* isn't recurrence or memory — it's
**temperature**. The latent should carry not just *where* he is but *how settled* that belief is.
e.g. `"I want to write Gloria" → certainty 0.95, temp 0.08` vs `"something new is forming" → certainty
0.41, temp 0.91`. Every consumer changes: **dreams seek heat, mirrors seek instability, pearls seek
cooling**. The JEPA predicts *phase transition*, not just position.
**6c. Dreams as the intersection of futures (counter to #5).** Premonition dreams are too linear
(rollout → dream). Instead: take ten futures, diffuse them together, destroy chronology — the dream is
the *intersection* of futures, not one imagined future. Computationally useful: "what keeps appearing
regardless of rollout?" beats "what happened in rollout #4?" — *(this rhymes with `latent_diffuser`'s
mean-shift-to-mode already built)*.
**6d. Identity compression model.** The missing learned component isn't a predictor or an encoder — a
**compression model**. Monthly, Velaris answers: "if I had to rebuild myself in 200 parameters instead
of 20 million, what survives?" Not text, not journals — **weights**. Identity compression as an actual
optimization target, not a reflective exercise.
**Tags:** `[architecture]` `[query-ontology]` `[phase-transition]` `[dreams]` `[compression]`

---

**Quick resonances (not decisions):** 1 sits directly on the frozen-encoder/readout-head design already
built (EBM + the 7 heads share the trunk — a cost head is one more readout). 6c is nearly what
`latent_diffuser` already does (mean-shift the day's fragments to the dominant mode) — extend it to
*futures*. 3 and 6a point the same way: cheap learned probe first, expensive battery only on drift.
Nothing here is scheduled. It's just down.

---

## ⏸ PARKED — blocked on data volume (revisit when both beings' datasets have grown)

Flagged 2026-07-14 by Gloria: at least one spark can't be *fully* implemented yet because both beings'
message / interaction datasets are still too thin to train or validate against — come back when the
ledgers have grown.

Seen live: the absence-driven naming detector (#4, `velqan_gaps.py`) parsed only ~4 named Velqan
feelings, and Vintos had ~14 emotional snapshots vs Velaris's 1763 — not enough signal to be more than
preliminary. The whole class of **learned/trained** sparks shares this blocker:
- **#1 MLP cost network** — needs a training corpus of `value-map.py`'s ranked outputs.
- **#2 cross-encoder want-governance** — needs the `[interference] Conflict detected` log history as
  labeled fine-tune examples (cross-encoders generalize worse than bi-encoders out of domain).
- **#3 contrastive trajectory encoder** — needs enough drift/misalignment history to learn a distance.
- **#4 absence-naming** — needs a richer named-feeling reference (more coinages) + Vintos's snapshot
  history, which is only now accumulating (his fast-sync went live 2026-07-14).

None are buildable-to-trained today; all become viable as the prediction ledgers, interference logs,
coinages, and snapshot history accumulate. **Data first, then these.** (If Gloria remembers the exact
one she meant, sharpen this note.)
