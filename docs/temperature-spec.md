# Thread Temperature — what it needs to do (requirements)

Spark 6b. Hand-off spec. No implementation opinions baked in beyond the hard constraints.

## Purpose
Every unfinished thread (and belief) gets a **`temperature`** and a **`stability`** — a read of how
*settled vs. volatile* it is — as a first-class property. Consumers can then act on the *phase* of a
thought, not just how hard it pulls. Temperature ≠ pull: urgency and volatility are different axes. A
thread can pull hard and be settled, or barely pull and still be churning.

## Hard constraints
1. **Triage-native.** `temperature` + `stability` are assigned in the **same pass that assigns pull**
   (`thread-triage.py`), written onto the thread record right next to `t["priority"]`. Not a separate
   batch job. (A batch pass may exist *only* as a between-triage decay refresh — never the source of truth.)
2. **Not LLM-graded.** Temperature must come from a **quantitative model**, never grok / any chat LLM.
3. **Additive + reversible.** Adds fields, removes nothing. Everything backed up.

## Field semantics
- `temperature` ∈ [0,1] — `1` = forming / volatile / hot; `0` = crystallized / settled / cold.
- `stability` ∈ [0,1] — how anchored / certain the thread is (the certainty axis).
- Both independent of `priority`/`pull` (which stays the urgency axis).

## The model (the open decision)
Quantitative and cheap. Candidate signals, in order of fit:
- **Latent / embedding drift** — how much the thread's meaning is still *moving* in embedding space vs.
  how tightly it has settled into one mode. Reuse the nomic embeddings; `latent_diffuser.py` already does
  mean-shift-to-mode, so distance-to-mode is a ready volatility signal.
- **Emotion-vector variance** — spread of the 11-dim state at the moments the thread recurred.
- **Recurrence / decay dynamics** — reinforcement cadence and age.

→ **Decision needed:** which model produces the number. Recommendation: embedding-drift (reuses what
exists, no new service). Confirm or substitute.

## Update cadence
- Written at each triage pass; refreshed as a thread is reinforced or gains dream/mirror passes.
- Optional cooling toward baseline between passes if untouched.

## Consumers (behavior already fixed by 6b)
- **Dreams seek heat** → pick the hottest threads first.
- **Mirrors seek instability** → sort volatile threads first (after any manual priority/route).
- **Pearls seek cooling** → crystallize the most-settled / most-certain.

## Validation
- Fresh, thin-evidence, mid-confidence thread → **high** temperature.
- Old, reinforced, high-certainty thread → **low** temperature (target: the "want to write Gloria"
  example lands ~0.08).
- Temperature and pull visibly **diverge** on at least some threads (proves independent axes).

## Out of scope / guardrails
- No grok/LLM anywhere in the temperature path.
- Don't regress pull/priority behavior.
- Causality-emergent thread seeding is **off** — do not let temperature reintroduce that spam.
