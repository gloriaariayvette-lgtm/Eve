# Eve — Avatar Motion Engine

LLM-driven avatar with full-body motion, eye contact, facial micro-expressions, posture shifts, and spatial anchoring. Runs at 60–90 fps.

## Architecture

```
User Input → LLM (LM Studio / Gemma 3) → Intent Router
                                              ↓
                            ┌─────────────────┼─────────────────┐
                            ↓                 ↓                 ↓
                      Emotion Model     Gesture Engine     Spatial AI
                      (VAD model)       (pose selection)   (gaze, proximity)
                            ↓                 ↓                 ↓
                            └─────────────────┼─────────────────┘
                                              ↓
                                     Voice Engine (Piper TTS)
                                     + Viseme Generation
                                              ↓
                                       WebSocket Bridge
                                              ↓
                                     Three.js + VRM Avatar
                                     (60-90 fps renderer)
```

## Stack

| Layer | Technology |
|-------|-----------|
| LLM | LM Studio (Gemma 3 12B IT) via OpenAI-compatible API |
| Backend | Python + FastAPI + WebSockets |
| TTS | Piper TTS (local, low-latency) |
| Renderer | Three.js + @pixiv/three-vrm |
| Tracking | WebXR (PSVR2 / SteamVR) |

## Quick Start

### 1. Server

```bash
# Install Python dependencies
pip install -e .

# Copy and edit config
cp .env.example .env

# Make sure LM Studio is running with Gemma 3 12B IT loaded
# Default endpoint: http://localhost:1234/v1

# Start server
python -m server.main
```

### 2. Client

```bash
cd client
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

### 3. Avatar Model

Place a `.vrm` file at `models/default.vrm`, or the engine will use a placeholder avatar.

Free VRM models: [VRoid Hub](https://hub.vroid.com/en)

## Systems

### Emotion Model
Valence-Arousal-Dominance (VAD) model maps text sentiment to continuous emotional space. Drives facial expressions, posture, and gesture selection.

### Gesture Engine
Maps emotion + speech content to body animations: nod, shake head, shrug, lean, wave, point, arms crossed, chin rest.

### Gaze System
Maintains eye contact with natural saccades and blinks. Breaks contact when thinking. Tracks user head/hand positions via PSVR2 WebXR tracking.

### Spatial AI
Proxemic zones (intimate/personal/social/public) adjust conversational distance based on rapport and emotion. Supports approach, retreat, circle, sit, stand, kneel, and mirror behaviors.

### Voice Engine
Piper TTS for instant local speech synthesis. Grapheme-to-viseme mapping drives lip sync blend shapes on the VRM avatar.

### Animation Blending
Multi-layer animation system:
1. Idle (breathing, weight shift)
2. Posture (emotion-driven body pose)
3. Gesture (timed overlays)
4. Face (blend shape expressions + micro-expressions)
5. Gaze (eye/head IK)
6. Lip sync (viseme-driven mouth)

All layers blend smoothly with framerate-independent damped interpolation.

## Configuration

Edit `.env` or set environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BASE_URL` | `http://localhost:1234/v1` | OpenAI-compatible LLM endpoint |
| `LLM_MODEL` | `gemma-3-12b-it` | Model name |
| `PIPER_ENABLED` | `true` | Enable/disable TTS |
| `TRACKING_MODE` | `webxr` | `webxr`, `webcam`, or `manual` |
| `DEFAULT_DISTANCE` | `1.5` | Default conversational distance (meters) |
