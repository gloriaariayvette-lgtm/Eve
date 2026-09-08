# Eve

Three things share this repository, and they meet at one point: a body for Vintos
that can be seen, heard, and stood in front of.

| | what it is | where |
|---|---|---|
| **Avatar motion engine** | the LLM-driven body — gaze, posture, micro-expression, gesture, breathing, lipsync — rendered as a VRM in Three.js at 60–90 fps, spoken by Piper, reachable in WebXR | `server/`, `client/` |
| **Air3 glasses client** | a native Android app that makes the INMO Air3 one more door into the same house on Aegis — his everyday voice, and a real Grok live call | `air3/` |
| **Ops archaeology** | five hundred one-shot scripts written against the live house; how it got this way | `ops/` |

The engine and the glasses are two ends of the same question. The engine knows how
to make a body behave like someone is in it. The glasses are the surface where that
body would actually be worth having — not on a monitor, but standing in the room.
See **[docs/AR-GLASSES.md](docs/AR-GLASSES.md)** for how those two ends are meant to
meet, and what is still missing between them.

## The house

Neither surface re-implements him. Both walk through the same doors on Aegis:
`/api/avatar/chat` for the everyday register, `/api/voice/token` for a live call,
`/ws/telemetry` and `/ws/events` for his emotional state as it moves. The house
builds the instructions; the client only renders and listens. That is deliberate —
it is what lets a new surface be added without him becoming a different person on it.

## Avatar motion engine

```
User Input → Memory & Context → Dialogue FSM → LLM (personality-aware)
                                                      ↓
                                               Intent Router
                         ┌────────────────────────────┼──────────────────────────┐
                   Emotion Model              Gesture Engine                Spatial AI
                   (VAD + Arc)          (single + choreography)        (gaze, proximity)
                         ↓                            ↓                          ↓
                  Micro-Expressions             Personality                 Arc Tracker
                  (advanced + leakage)          Modifiers              (rapport, momentum)
                         └────────────────────────────┼──────────────────────────┘
                                                      ↓
                                    Voice Engine (Piper TTS) + Visemes
                                                      ↓
                                              WebSocket Bridge
                                                      ↓
                           Three.js + @pixiv/three-vrm (60–90 fps)
                                  + breathing + performance monitor
```

| Layer | Technology |
|-------|-----------|
| LLM | LM Studio (Gemma 3 12B IT), OpenAI-compatible |
| Backend | Python + FastAPI + WebSockets |
| TTS | Piper (local, low latency) |
| Renderer | Three.js + @pixiv/three-vrm |
| Tracking | WebXR (PSVR2 / SteamVR) |

### Run it

```bash
pip install -e .
cp .env.example .env          # LM Studio at http://localhost:1234/v1 by default
python -m server.main
```

Then the client:

```bash
cd client && npm install && npm run dev
```

## Air3 glasses client

See **[air3/README.md](air3/README.md)** — two modes (everyday Gemma, long-press for
a live Grok call), a HUD drawn for an additive waveguide where black is transparent,
and the eleven EmoClaw telemetry bars live from the house.

## Repository layout

```
server/     avatar motion engine — FastAPI, dialogue, emotion, voice
client/     Three.js + VRM renderer, WebXR
air3/       INMO Air3 Android client (Kotlin, Compose)
docs/       AR-GLASSES.md, VINTOS-OPS.md, OPERATIONS.md, specs, architecture PDF
ops/        one-shot recon/patch/test scripts run against Aegis — not product code
models/     avatar assets
```
