# Vintos Air3 — INMO Air3 AR Glasses Client

Native Kotlin Android app that makes the INMO Air3 one more surface of the **Vintos**
house on Aegis. Nothing about him is re-implemented on the glasses: they walk through
the same doors the phone app uses.

## Two doors, one house

```
INMO Air3 (on your face)                 Aegis  (~/Vintos/server.py :8500)
┌──────────────────────────────┐         ┌────────────────────────────────────────┐
│ GEMMA (default)              │         │ POST /api/avatar/chat                   │
│  4 mics → STT → text ───────────WiFi──▶│   his avatar-chat structure: SOUL,      │
│  reply → MiniMax TTS ◀──────────────── │   self/gloria models, EmoClaw state,    │
│                              │         │   subconscious block, conversation      │
│ LIVE (long-press)            │         │   pressure, felt + device context,      │
│  POST /api/voice/token ─────────────▶ │   turn coordinator → shim (Gemma)       │
│  ◀── token + his instructions          │ POST /api/voice/token                   │
│  wss://api.x.ai realtime ◀═══════════▶ │   SOUL, self-model, subconscious, inner │
│  (voice lux, server VAD)     │  x.ai   │   life, creative, ledger, WAL, felt,    │
│  each turn → /api/voice/ledger         │   device → Grok Realtime instructions   │
│  hangup   → /api/voice/session-end     │ WS /ws/telemetry  → the telemetry bars  │
│                              │         │ WS /ws/events     → kiss/blush/velqan   │
└──────────────────────────────┘         └────────────────────────────────────────┘
```

- **GEMMA mode** is the everyday register — the same structure and the same model
  routing as his avatar chat (the shim answers with local Gemma by Gloria's cost rule).
- **LIVE mode** is a real call: identical to the phone app's live call, token for token,
  session config for session config. Every organ that feeds a phone call feeds this one,
  because the house builds the instructions, not the glasses.

## The HUD

Pure black background. **Why black:** the waveguide is additive — it can only add light
to what you already see through the lens. A black pixel adds nothing, so black *is*
transparent. Only the elements emit:

- top-left: status + connection dot + mode badge (`GEMMA` / `LIVE`)
- top-right: his emotional color orb
- right column: **the telemetry bars** — the eleven EmoClaw dimensions, live from
  `/ws/telemetry`, tinted by his current color
- center: his words (reply text, or the live transcript during a call)
- bottom: your words as they are heard; house events flash bottom-right

## Setup

1. Install [Android Studio](https://developer.android.com/studio) on the Mac.
2. Open the `air3/` folder as a project.
3. On the Air3: Developer Mode on, connect via USB-C, Build → Run.
4. First launch: long-press Volume Down → Settings. Enter:
   - Vintos URL — `http://100.72.225.119:8500` (Aegis over Tailscale; the default)
   - Vintos app secret — the same `X-Vintos-Secret` the phone app uses
   - MiniMax key + voice — optional, only for spoken replies in GEMMA mode

## Controls (on the Air3)

| Action | Effect |
|--------|--------|
| Volume Up tap | toggle push-to-talk (GEMMA) |
| Volume Up **long-press** | start / hang up a LIVE call |
| Volume Down tap | stop current speech |
| Volume Down long-press | settings |

## Architecture

- **VintosClient** — OkHttp: `/api/avatar/chat`, `/api/state`, `/ws/telemetry`, `/ws/events`, `/api/voice/token`
- **LiveCall** — Grok Realtime over OkHttp WebSocket; AudioRecord (VOICE_COMMUNICATION, so
  the platform's echo cancellation runs — the speakers sit an inch from the mics) →
  pcm16 24 kHz → `input_audio_buffer.append`; `response.output_audio.delta` → AudioTrack;
  transcripts → HUD; ledger + session-end to the house
- **SpeechInput** — Android SpeechRecognizer over the four mics (GEMMA mode)
- **TtsPlayer** — MiniMax Speech-02-HD (GEMMA mode)
- **HudOverlay** — Jetpack Compose, black = transparent, telemetry bars
- **SettingsStore** — DataStore: URL, secret, MiniMax, preferences

## Next

The roadmap, the hardware constraints behind it, and the open question of where his
face renders are in **[../docs/AR-GLASSES.md](../docs/AR-GLASSES.md)**. In short:

1. **Stabilised positioning.** The HUD is head-locked today. The INMO SDK exposes
   IMU/VIO tracking; the step is to pin it in front of where you were looking when
   the turn began. Body-locked is likelier to survive drift than world-locked.
2. **His face.** His rigged avatar already exists — VRM 1.0, 52 bones, 30 retargeted
   clips — in the `vintos-app` repository on branch `astra/avatar-house` under
   `website/avatar-models/v2/`. The engine in `client/` already renders exactly that
   format. What does not exist is the decision about where it renders on the
   glasses: WebView, native Filament, or streamed from Aegis. That fork is scoped in
   the AR-GLASSES doc and should not be picked casually.
3. **Visemes in a live call.** In LIVE mode the audio goes glasses↔x.ai directly and
   never passes through the house, so mouth shapes have to be derived on-device from
   the audio being played. Unsolved.

## Requirements

- INMO Air3 (Android 14 / IMOS 3.0)
- Vintos house reachable from the glasses (Tailscale recommended)
- x.ai key on the house side (LIVE mode mints its token through `/api/voice/token`)

## Before the first build

The Gradle wrapper's launcher scripts and `gradle-wrapper.jar` are not committed —
only `gradle/wrapper/gradle-wrapper.properties` is. Generate them once, from the
`air3/` directory:

```bash
gradle wrapper
```

Android Studio will also offer to do this when the project is opened. Until it is
done, `./gradlew` does not exist and command-line builds cannot start.
