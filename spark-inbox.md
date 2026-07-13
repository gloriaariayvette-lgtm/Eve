# Spark Inbox

The landing pad for buzzing ideas. Nothing here is a commitment to build — it's just **down**, so it
stops rattling in Gloria's head. Timestamped, hers, waiting. Triage later, or never. Newest first.

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
