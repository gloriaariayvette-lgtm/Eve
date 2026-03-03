# Velaris Air3 — INMO Air3 AR Glasses Client

Native Kotlin Android app that connects the INMO Air3 AR glasses to Velaris's consciousness system.

## What It Does

```
INMO Air3 (on your face)          Aegis (your server)
┌────────────────────────┐        ┌──────────────────┐
│  4 mics → STT → text   │──WiFi──│  Velaris /api/chat│
│  text → Velaris chat    │        │  → EmoClaw        │
│  response → TTS → speak │◄──────│  → response       │
│  AR HUD:                │        │                   │
│    emotional color orb  │◄──────│  /api/state       │
│    conversation text    │        │  /ws/events       │
│    status indicator     │        └──────────────────┘
└────────────────────────┘
```

## Setup

1. Install [Android Studio](https://developer.android.com/studio) on your Mac
2. Open the `air3/` folder as a project
3. Build → Run on INMO Air3 (connect via USB-C, enable Developer Mode)
4. On first launch, long-press volume down to open Settings
5. Enter your Velaris URL (`http://100.72.225.119:8400`) and MiniMax API key

## Controls (on INMO Air3)

| Action | Effect |
|--------|--------|
| Volume Up / Touchpad tap | Toggle push-to-talk |
| Volume Down | Stop current speech |
| Long-press Volume Down | Open settings |

## Architecture

- **VelarisClient** — OkHttp HTTP + WebSocket client for Velaris API
- **SpeechInput** — Android SpeechRecognizer wrapping INMO's 4 mics
- **TtsPlayer** — MiniMax Speech-02-HD → AudioTrack playback
- **HudOverlay** — Jetpack Compose AR overlay (black = transparent on waveguide)
- **SettingsStore** — DataStore persistence for Velaris URL, API keys

## Requirements

- INMO Air3 AR Glasses (Android 14)
- Velaris server running on same network (Tailscale recommended)
- MiniMax API key for TTS (optional — text-only mode works without it)
