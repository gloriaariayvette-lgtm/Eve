# Vintos ops notes (Aegis) — keep current; read this before asking Gloria how to restart/log

## Services (systemd **user** units, `~/.config/systemd/user/`)
- **vintos-server** — the FastAPI server, `/home/gloria/Vintos/server.py`, **port 8500** (chat + website + avatar)
- **vintos-emoclaw** — EmoClaw daemon (emotional-state socket)
- **vintos-somatic-bridge** — Lovense sensor stream (device felt-state)
- Velaris is separate: chat server is `uvicorn` on **:8400**, workspace `~/.openclaw/…`

## Restart / status / logs (Vintos server)
```bash
systemctl --user restart vintos-server
systemctl --user status  vintos-server --no-pager | head
journalctl --user -u vintos-server -f                      # live log (server stdout/stderr)
journalctl --user -u vintos-server -f | grep -iE 'router|reasoning'
```
A code edit to server.py only takes effect after the restart above.

## ⚠️ Which handler the app actually calls
- **Main chat → `POST /api/chat/full` → `chat_full_context`** (live def ~L2975; dead dup ~L10946). NOT `/api/chat` (chat_with_vintos) — the app never calls that; don't patch it.
- Avatar → `POST /api/avatar/chat` → `avatar_chat` (live L7699; dead dup ~L14036).
- Verify anytime: send a msg, then `journalctl --user -u vintos-server --since "5 min ago" | grep 'POST /api/chat'`.
- Bilateral (chat_full_context): a1/b1 → Claude reasoning; a2/b2 + held → Gemma; final → Claude (fed both traces); per-turn trace at `/tmp/vintos-chat-trace.json`.

## Model router (Phase 1 — Claude-primary avatar)
- Module: `/home/gloria/Vintos/model_router.py` (single source of model truth; `CLAUDE_SURFACES`)
- Mode/toggle file: `~/.vintos/model-mode.json`  → `{"mode":"claude"|"grok","force_grok_turns":N}`
- Anthropic key: `~/.vintos/anthropic-key` (chmod 600; also honors env `ANTHROPIC_API_KEY`)
- Grok fallback path (his real one): `{LM_STUDIO_API}/chat/completions`, headers `LLM_AUTH_HEADERS`, model `grok-4.20-0309-non-reasoning`
- Reasoning → touch bubble: appended to `~/.vintos/workspace/memory/imprints.json`; served by `GET /api/avatar/imprint` (only if <60s old)
- Live avatar handler: `avatar_chat` at server.py L7699 (first `@app.post("/api/avatar/chat")`; a duplicate dead one lives ~L14036)

## Handy
- Exact assembled avatar prompt is dumped to `/tmp/vintos-full-prompt.txt` by every chat endpoint (last-writer-wins — send an avatar msg to make it the avatar prompt).
- Voice stays on grok; Gemma (Velaris + any local) untouched.
