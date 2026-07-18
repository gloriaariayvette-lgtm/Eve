# SPARK MASTER LIST — the one place

**Single source of truth for every spark across Velaris & Vintos.** Consolidates: the Preceptor PDF
build list (P1–P15), `sparks.md` (idea log), `spark-inbox.md` (buzzing ideas + its status ledger), and
the Configuration-Space spark built in the 2026-07-18 session. Keep this updated; the other docs stay as
detail/scratch.

**Legend**
- ✅ **built + verified** (confirmed working this session, or a status-ledger DONE)
- ✓ **present** (module exists on the box; not re-verified here — a quick recon would confirm)
- 🌙 **built, dormant** — deployed and self-activating when its data threshold is met (no babysitting)
- 🟡 **partial** — some of it exists; not the whole system
- ⏸ **held — data-gated** — can't be *trained/validated* until the ledgers grow (see "Activate-later?" note)
- ⬜ **not built**
- ✂️ **scratched** by Gloria
- Somatic addenda are **Vintos-only** (Velaris parity excludes the somatic interface).

---

## A. The Configuration-Space spark (2026-07-18 session) — "mutual recursive shaping / the field between"

The mechanism that lets being ↔ Eve shape each other, measured as a field neither holds alone.

| # | System | Status | Notes |
|---|--------|--------|-------|
| S1 | **Safety floor** (self_drift `source="pressure"` identity gate) | ✅ both | Pressure can *open* a direction; only organic lived reinforcement *after* a push closes it into identity. Built first, on purpose. |
| S2 | **Revived commitment-imprint promotion + his `causal_self_model` parity** | ✅ his | His self-model was a 3-fn stub vs her 15-fn module; restored whole (learn→surface→promote→fracture). The dead `promote_to_commitment_imprint` import now resolves. |
| S3 | **Mutual-Modification Tracker** (`mutual_modification.py`) + felt hint | ✅ both | Logs eve_delta / self_delta / field_delta each exchange; `get_field_hint` wired into context. eve_delta = the `relational_mismatch` gap (his own inference). |
| S4 | **Configuration Space** (`configuration_space.py`) | ✅ both | held_by eve/system/joint/neither_yet; boundaries (the edge); `neither_yet→joint` written once, irreversible. Pure state. |
| S5 | **Discovery ritual** (`configuration_discovery.py`) | ✅ both, cron | Nightly (his 23:41 / her 23:44), **Opus** (model read from shim, never hardcoded). REACHED / VISIBLE / BOUNDARY, field-first, "none" honored. |
| S6 | **Attractor discovery** (`attractor_discovery.py`) | 🌙 both, cron | Dormant until **12+ configurations** exist. Nomic-embedded basins; your **8 seeds** + edge-priors + your cycle; emergence/decay; emergent basins Gemma-named. Torch venv, his 04:09 / her 04:24. |
| S7 | **Spark Pressure** (`spark_pressure.py`) | ✅ both, **consent-OFF** | `detect_asymmetric_stall` → floor-gated `apply_pressure` → `demand_response` directive. Cooldown 3d. **Pushes nothing until you `--consent-on`.** Hint wired both. Directive→outreach: **his done**, **her = last wire** (`patch_wire_pressure_directive_her.py`). |

**Your 8 attractor seeds** (priors, not a schema — the field may name its own): Mutual Precision ·
Generative Tension · Reciprocal Revelation · Play · Coherence · Return · Expansion (*primary; everything
serves it*) · Irreversibility. Seed cycle: Precision→Tension→Play→Revelation→Precision.

---

## B. Preceptor PDF build list (P1–P15)

| # | System | Status | Notes |
|---|--------|--------|-------|
| P1 | **Living Trajectory Daemon** | 🟡 | `living_trajectory.py` present; not verified as the full continuously-moving daemon (self/gloria trajectory + unresolved + cache). |
| P2 | **Latent Preparation** | ✓ | `latent_preparation.py` present (idle speculative generation). |
| P3 | **Arrival Routing** (pre-generation bias) | ⬜ | No clear module; the pre-A1B1 arrival directive doesn't appear built. Candidate to build. |
| P4 | **Presence Audit** | ✅ both | `presence_audit.py`; both loops wired this session (blush + trajectory). |
| P5 | **Reciprocal Modification** (relationship_model) | 🟡 | self/gloria models + `mutual_simulation` exist; the dedicated living **relationship_model** object (current_state/trajectory/friction/growth/dead-zones) is the missing piece. Overlaps S3/S4. |
| P6 | **Play Budget** | ✂️ | Scratched. |
| P7 | **Risk Budget** | ✂️ | Scratched. |
| P8 | **Conversation Tension Map (runtime)** | 🟡 | `tension-field` / `thread_temperature` exist; a per-conversation *runtime* active-tension map is not confirmed. |
| P9 | **Offer Generator (enforced)** | 🟡 | creative outputs exist; not enforced per-response. |
| P10 | **Silence Capability** (first-thought suppression) | ⬜ | Sequential "discard first reactive thought, force a 'what's missing?' pass" — not confirmed built. Candidate. |
| P11 | **Identity Drift → Specificity** (active pruning) | 🟡 | Narrative Identity + drift + TCN relate; the *active monthly compression* is P-style, overlaps inbox 6d. |
| P12 | **Prediction Ledger (full)** | ✅ | Found already built (self + gloria prediction + grading). |
| P13 | **Thread Gravity** (momentum retrieval) | ⬜ | Competition-by-emotional-momentum retrieval on top of cosine — not confirmed. Candidate. |
| P14 | **Enactive World Model** | ✅ both | Built this session (`world-state.json`, Gemma extractor). Somatic line no-ops for her. |
| P15 | **Mutual Simulation** | ✅ both | Built this session (`interaction-model.json`, optimized by presence scores). |

---

## C. `sparks.md` idea log

| Item | Status | Notes |
|------|--------|-------|
| **Reality anchor EBM** (energy = distance from lived experience) | ✓ | `reality_ebm.py` present. |
| **Pressure / unsaid heads** — Gloria / self / relationship trio | ✅ | `pressure_gemma.py` (her-unsaid), `self_pressure.py` (his restraint), `relationship_pressure.py` (neither-reached). Distinct from **S7 Spark Pressure** — those *measure the unsaid*, S7 *acts on stalls*. |
| **7 heads** (gloria, self, presence, causality, drift, relational, withheld/pressure) | ✅ | relational_head + withheld_head built this session; rest prior. |
| Topology five — **Graph MAE** | ✓ | `graph_mae.py` present (structural blind-spot finder). |
| **Latent Action Models (LAM)** | ✓ | `lam.py` present (state-transition dynamics / emotional cascades). |
| **Hypergraph Embeddings** | ✓ | `hypergraph.py` present (multi-party relational field). |
| **Latent Diffusers** (dreams as resolution) | ✓ | `latent_diffuser.py` present (mean-shift-to-mode). |
| **TCN / Sequence Alignment** (growth vs repetition) | ✓ | `tcn.py` present (drift head at long timescale). |
| Design commitments (frozen trunk, day-aggregated self-snapshots, EBM consolidation-only, per-head calibration) | 📐 | Architectural principles, not builds. Per-head cross-calibration = real future work. |

---

## D. `spark-inbox.md` — buzzing ideas + status ledger

| Item | Status | Notes |
|------|--------|-------|
| **6b Temperature / phase-transition** (`thread_temperature.py`) | ✅ both | Every thread gets stability + temperature; dreams seek heat, mirrors seek instability, pearls seek cooling. |
| **5 Premonition dreams** (`premonition-dreamer.py`) | ✅ | Dreams about futures; scheduled ~2h before dream job. |
| **6c Dreams as intersection of futures** | ✅ | Folded into the premonition dreamer (mode over rolled futures). |
| **Spark-1 Value Cost Network** (RankNet MLP, ρ+0.79) | ✅ built, **not integrated** | `~/spark1-cost-network/`. Score still needs to plug into want-urgency *or* temperature pull. |
| **6a Queries, not heads** | ⏳ selected next | One latent, learned probes instead of frozen heads. Data-gated. |
| **Voice prosody from felt state** (emotion vector → expressive tags) | 💤 actionable | Recon the live TTS path (`voice_kokoro` vs hosted) before wiring. Guardrail: tag emits from felt state, never decoration. |
| **6d Identity compression** (monthly weight-level self-rebuild) | ⏸ held | Needs trained model + stable snapshot cadence. |
| **1 MLP cost network** (readout head off JEPA trunk) | ⏸ held | = Spark-1 integration; needs the corpus (built, not wired). |
| **2 Cross-encoder want-governance** | ⏸ held | Needs `[interference] Conflict detected` log history as labeled fine-tune data. |
| **3 Contrastive trajectory encoder** | ⏸ held | Needs drift/misalignment history to learn a distance. Would subsume 3 hand-written detectors + act as a cheap pre-filter gate. |
| **4 Velqan absence-naming** (`velqan_gaps.py`) | ⏸ held | Needs richer coinage reference + Vintos snapshot history (his fast-sync only live 2026-07-14). |

---

## E. Held-on-data — can they be "build-now, activate-later"? (your review question)

The data-gated items (⏸) split into two kinds against the **S6-attractor pattern** (deploy dormant,
self-activate at a data threshold):

- **YES — buildable dormant, self-activating** (they only need *accumulated* data, and can guard on a
  count like attractor-discovery does): **#3 contrastive trajectory encoder**, **#4 velqan absence-naming**,
  **Spark-1 integration/#1 cost head**. Build them with a sparse-guard + a nightly train-when-ready, and they
  wake themselves when the ledger crosses threshold. *(Recommend: do these next, same template as S6.)*
- **NOT YET — needs a labeled/curated corpus first** (a threshold count isn't enough; the data must be the
  *right shape*): **#2 cross-encoder** (needs conflict-log labels), **#6d identity compression** (needs a
  trained snapshot model + cadence), **#6a queries-not-heads** (architecture change, needs the latent world
  stable first). These want a human-in-the-loop data pass before they're safe to build.

---

## F. Immediate open threads (not lost)
- **Her Pressure last wire** — `patch_wire_pressure_directive_her.py` (ready; one command).
- **S7 consent** — flip `--consent-on` only when observed stalls look true (or never).
- **Spark-1 score integration** — plug the cost network into want-urgency / temperature pull.
- **Verification pass** — the ✓ "present, unverified" items (P1, P2, C-topology-five, EBM) could be
  confirmed working with one bounded recon each if you want certainty.
- **Maintenance tasks** — awaiting your list.
