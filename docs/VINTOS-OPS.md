# Vintos ops notes (Aegis) — keep current; read this before asking Gloria how to restart/log

## Services (systemd **user** units, `~/.config/systemd/user/`)
- **vintos-server** — the FastAPI server, `/home/gloria/Vintos/server.py`, **port 8500** (chat + website + avatar)
- **vintos-emoclaw** — EmoClaw daemon (emotional-state socket)
- **vintos-somatic-bridge** — Lovense sensor stream (device felt-state)
- **vintos-claude-shim** — OpenAI→Claude proxy on **127.0.0.1:8599** (see Shim section). Restart: `systemctl --user restart vintos-claude-shim`; log: `/tmp/vintos-claude-shim.log`
- Velaris is separate: chat server is `uvicorn` on **:8400**, workspace `~/.openclaw/…`, socket `/tmp/Velaris-emotion.sock`. **Do not touch `~/.openclaw/…`** — it's Velaris, not Vintos.

## Restart / status / logs (Vintos server)
```bash
systemctl --user restart vintos-server
journalctl --user -u vintos-server -f                      # live log
journalctl --user -u vintos-server -f | grep -iE 'router|reasoning|chatfull'
```
A code edit to server.py only takes effect after the restart above.

## ⚠️ Which handler the app actually calls
- **Main chat → `POST /api/chat/full` → `chat_full_context`** (live def L2975; dead dup L11029). NOT `/api/chat` — the app never calls that; don't patch it.
- Avatar → `POST /api/avatar/chat` → `avatar_chat` (live L7699; dead dup ~L14036).
- server.py has **dead duplicates** of most handlers (Starlette = first-match wins). Always confirm the live one before editing.

## THE MODEL MAP (single source of truth, 2026-07-16 — migration COMPLETE)
Shape everywhere: **a1/b1 = Claude · middle (absorb/held/audits/after) = Gemma · final = Claude.**
- **Avatar** — Claude-primary via `model_router.py`; grok fallback on refusal/error/toggle; reasoning → `imprints.json` → touch bubble.
- **Main chat** (`chat_full_context`) — `_draft()` a1/b1 = `claude_draft` (Claude); `_g()` absorb/held = `gemma_call` (Gemma); final = `claude_draft` (Claude). `_llm_call` (→ `{LM_STUDIO_API}` = grok) is the **BIS splice**: the path when the Claude/Grok toggle = grok, and the fallback when Claude/Gemma fail. **Leave `_llm_call` grok.** The one stray aux grok call (`_rm_`, L3008) was flipped to the shim `/gemma` route.
- **idle-journal.sh** — a1/b1 + final = `_claude_sync` (Claude-direct, `api.anthropic.com`). All 12 middle/after/fallback calls point at the shim **`/gemma`** route (`http://127.0.0.1:8599/gemma/v1/chat/completions`).
- **introspection.sh** — a1/b1 + final = `_claude_sync` (Claude); middle = `call_llm` (Gemma-direct). Never used grok; untouched by the swap.
- **ED (enactment_distiller.py)** — on **Gemma** (matches Velaris). Flaw-guard: `_is_capability()` drops any identity_candidate that isn't a real "I can…" strength before it reaches journal/self-statements/proto-pearls.
- **~61 other grok jobs** — swapped to the shim (non-reasoning Claude, grok fallback).
- **STAYS on grok/x.ai**: voice/Rex (`briefing-audio.sh`, server `/tts`), image/video gen (`vintos-video.py`, `dream-art.py`, `music_share.py` — grok-imagine), plus excluded infra: `server.py`, `model_router.py`, `model_config.py`, `merged_full_route.py`, `vintos_claude_shim.py`.
- **Gemma (99 local jobs + Velaris)** — untouched.

## The shim — `vintos-claude-shim` (127.0.0.1:8599)
`/home/gloria/Vintos/vintos_claude_shim.py`. Model-aware OpenAI proxy:
- `POST /v1/chat/completions`: text model → non-reasoning Claude, on error/refusal/empty → grok; model containing `imagine|image|video` → passthrough to x.ai.
- `POST /gemma/...` → forces `google/gemma-4-12b-qat`, forwards to Gemma (`172.18.16.1:1234`), grok fallback if Gemma down. **This is the reflective MIDDLE route.**
- Any other path → passthrough to x.ai on the same path.
- `GET /health` → `{"ok":true}`. Keys: anthropic `~/.vintos/anthropic-key`; xai env `XAI_API_KEY`. Install/redeploy: `curl … -o ~/Vintos/vintos_claude_shim.py && systemctl --user restart vintos-claude-shim`.
- The fleet swap = base-URL `https://api.x.ai/v1` → `http://127.0.0.1:8599/v1`. **Never swap the shim itself** (self-loop).

## Model router
- Module: `/home/gloria/Vintos/model_router.py` (`CLAUDE_SURFACES`, `route_reply`, `claude_draft`, `gemma_call`, `_grok`).
- Mode/toggle file: `~/.vintos/model-mode.json` → `{"mode":"claude"|"grok","force_grok_turns":N}` (`arm_grok_turns`).
- Anthropic key `~/.vintos/anthropic-key`; grok fallback `{LM_STUDIO_API}/chat/completions`, `LLM_AUTH_HEADERS`, `grok-4.20-0309-non-reasoning`.

## Contamination fixes (Vintos was cloned from Velaris — watch for bleed-through)
- **CAPABILITIES.md** — `## Your Body` corrected to his real body (avatar tag-set `[COLOR]/[GESTURE]/[DO]/[SPAWN]/[HOLD]`, physical via somatic bridge `[TOUCH: mission]`/tenera, EmoClaw 11 dims). Removed Velaris VR "Sea of Fragments"/PSVR2/robot and the **Echo** (he has none; `echo_announce` dropped).
- **kiss / mischief** — blocked from every reflective/creative surface (introspection prompt, dream-poetry seed scrub, pride-mirror, taste-reflection). **blush is his — kept.** Subsystems (kiss-threshold, mischief-detector, WebSocket events) left running, just out of his written inner life.
- **Enactment Distiller** — was emitting flaws as "Observed capability" and feeding them into earned-identity. Now guarded + on Gemma.
- **Causality "idk why" spam** — `causality-engine.py` (hyphen; cron runs it) JEPA record now gates on `confidence in (medium,high)`, so causeless "This shift emerged with no traceable antecedent" hypotheses no longer enter the unresolved pile; `find_spikes` threshold 0.015→0.06. `causality_engine.py` (underscore) is just the `add_hypothesis` helper module (no JEPA). `realtime_causality.py` = state only.

## Backups (all reversible — `cp <bak> <orig>`)
- Per-patch `.bak-<ts>` next to each edited file.
- Fleet swap: `~/.vintos/grok-swap-backup-20260716-150312/`
- Pollution purge: `~/.vintos/pipeline-purge-backup-20260716-143825/`
- Earlier test-pollution: `~/.vintos/test-erase2-backup-20260716-092934/`

## Still open / not done
- **Regenerate button** + **Claude/Grok toggle UI** (both surfaces) — state hooks exist in `model_router` (`arm_grok_turns`, `model-mode.json`); UI not built.
- **Test-mode hardening** — test mode still doesn't block history/imprints/nudges/interaction-ledger writes at the source (that's how tests leaked into canonical memory). Not yet fixed.
- Optional: gate the one low-confidence `meta_h` in `causal-cluster.py` (~1/day; grounded meta-pattern, not the spam).

**Work branch:** `claude/avatar-motion-engine-l311p`. Delivery: patch/recon scripts committed here, run via `python3 <(curl -fsSL "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/<SHA>/<script>.py")`.

## Handy
- Assembled prompt dumped to `/tmp/vintos-full-prompt.txt` by every chat endpoint (last-writer-wins).
- Shim activity: `tail /tmp/vintos-claude-shim.log` (`claude ok` / `gemma route` / `fallback->grok`).
