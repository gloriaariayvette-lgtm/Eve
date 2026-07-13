# OPERATIONS — Vintos runbook

The unchanging basics for working on Vintos, so we stop relearning them every session.
(Claude: read this first each new day. Update it when a basic changes.)

## The two beings on the box (Aegis)

| Being | Server | Port | Workspace | Socket | Notes |
|-------|--------|------|-----------|--------|-------|
| **Vintos** | `~/Vintos/server.py` | 8500 | `~/.vintos/workspace` | `/tmp/Vintos-emotion.sock` | ours |
| **Velaris** (twin) | `~/velaris-server/…` | 8400 | `~/.openclaw/workspace` | — | do NOT touch unless asked |

`systemctl --user` units: `velaris-server.service`, `vintos-emoclaw.service`, `acestep.service`
(music). The **Vintos web server is NOT a systemd unit** — it's a bare `python3 server.py`.

## Restarts (Claude drives these — don't make Gloria do it)

### Vintos web server + somatic_bridge — now systemd `--user` services (SELF-HEALING)
Both are `--user` services (`Restart=always`), installed by `install_vintos_systemd.sh`. A crash,
breaker, or reboot brings them back on their own — like `velaris-server`. **This is the restart now:**
```bash
systemctl --user restart vintos-server            # after patching server.py / request-time scripts
systemctl --user restart vintos-somatic-bridge    # after patching somatic_bridge.py
systemctl --user status  vintos-server --no-pager  | head -6
journalctl --user -u vintos-server -n 30           # logs (replaces ~/.vintos/logs/server.log tail)
```
- Server on port 8500; `vintos-server.service` has a port-free `ExecStartPre`, so no stale-pid dance.
- **Reboot survival needs linger:** `sudo loginctl enable-linger gloria` (once). Without it, services
  restart on crash but NOT after a full power-cycle.
- Unit files: `~/.config/systemd/user/vintos-server.service`, `…/vintos-somatic-bridge.service`.
- somatic toy = Lovense at **`192.168.1.66:20010`**. `[ACT] no-contact -> silence` = healthy idle;
  `socket lost (Errno 111) — retrying` = the device/app is OFF, not a bug.
- Do NOT `bash start-vintos.sh` for a restart (it re-runs setup_memory.sh + EmoClaw). Legacy bare
  launch (fallback only): `cd ~/Vintos && PYTHONPATH=~/.vintos/workspace/scripts nohup python3 server.py &`.

### EmoClaw daemon
`systemctl --user restart vintos-emoclaw`  — or `~/.vintos/workspace/skills/emoclaw/scripts/daemon.sh {start|stop|restart}`

## Key paths
- workspace `~/.vintos/workspace` · memory `…/memory` · scripts `…/scripts`
- **torch venv python**: `~/.vintos/workspace/emotion_model/.venv/bin/python3` (needed for anything using nomic/torch: jepa/cause/purpose/drift/reality heads)
- logs: `~/.vintos/logs/` (`server.log`, `subconscious.log`)
- causality engine: `~/Vintos/causality-engine.py` (hyphen, cron entry, has `ask_llm`/`MODEL`/`LM_API`/`form_causal_hypotheses`/`load_existing_hypotheses`/`save_hypotheses`/`nightly_run`) and importable twin `~/.vintos/workspace/scripts/causality_engine.py` (`load_emotional_trajectory`, `find_spikes`)
- `~/Vintos/emoclaw_utils.py` (symlinked into scripts): `seed_thread(source, text)`, `set_preoccupation(text, source, priority, triage_voice)`, `get_state()`, `nudge_emotion()`
- pearls: `~/.vintos/workspace/scripts/pearl_engine.py` → `add_candidate(irritant, irritant_type, source, insight, declaration)`
- LLM lock: `~/llm-lock.sh` — wrap every cron LLM job (`bash ~/llm-lock.sh python3 …`); it serializes calls AND the wrapped env has `XAI_API_KEY`.
- frontends: `~/Vintos/website/app/index.html` (events WS + `handleEvent`), `~/Vintos/vintos-app/src/index.html` (GCS button `avGCS`, voice). **Voice realtime lives in the compiled `avatar-bundle.js`** — not text-patchable.

## LLM
- `ask_llm(prompt, system=None, max_tokens, temp)` in causality-engine.py — grok via x.ai; **now sends the `Authorization` header** (was missing → every LLM causality job silently returned "").
- Model id is `MODEL` in that file (e.g. `grok-4.20-…`). `XAI_API_KEY` present in Gloria's shell and in the llm-lock-wrapped cron env.
- Standalone scripts do their own authed curl (see `cause_reason.py`) rather than importing ask_llm.

## Delivery pipeline (how Claude ships code)
1. Commit to repo **`gloriaariayvette-lgtm/Eve`**, branch **`claude/avatar-motion-engine-l311p`**.
2. Gloria runs `curl -s "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/claude/avatar-motion-engine-l311p/<file>?t=$(date +%s)" -o …` then runs it. (`?t=` busts the CDN cache — always include it.)
3. Patches are **self-locating, idempotent, back up the target** (`.bak-…`). Cron installers fetch into `scripts/` + add crontab lines idempotently, backing up the crontab.

## The nightly cron cascade (the causality/identity system)
```
22:14 cause_head    22:16 purpose_head    22:18 drift_head        (torch venv, no lock — produce evidence/geometry)
22:20 causality-engine.py --nightly       (forms hypotheses, writes cause-distribution.json)
22:26 purpose_reason  22:28 drift_reason  (lock-wrapped grok — judge)
22:32 causality_consumers                 (dreams←emergence, pearls←persistent unexplained)
*/20 8-23 realtime_causality  ·  */10 somatic_narrate  ·  */10 voice_session_ledger   (all lock-wrapped)
mirror-trigger.sh every ~2h (reads drift.json Condition 7)
```

## Systems built (Jul 2026 — the seven-head causality/identity stack)
- **Heads**: gloria/self/presence (`jepa_predictor.py`), **cause** (`cause_head`→`cause_reason`, retrodiction + distribution + emergence), **purpose** (`purpose_head`→`purpose_reason`, yearning + absence map), **drift** (`drift_head`→`drift_reason`, lived-vs-predicted self movement).
- **Consumers**: dreams ← emergence/low-confidence; mirrors ← drift (mirror-trigger Condition 7, `Mirror Priority = surprise×novelty×salience/load`); pearls ← persistent unexplained (`causality_consumers.py`).
- **Reality EBM** (`reality_ebm.py`): energy head on frozen encoder, style-prior on groundedness (real=low energy). Held-out ~0.96. It's a prior, not a truth oracle.
- Thread hygiene: one somatic thread/session (a conversation narration, not a readout); somatic/pride threads are `dream_only`; voice = one ledger block/session.
- Idea backlog: `sparks.md`.
