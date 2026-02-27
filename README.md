# Eve — Avatar Motion Engine

LLM-driven avatar with full-body motion, eye contact, facial micro-expressions, posture shifts, spatial anchoring, conversational memory, emotional intelligence, and personality. Runs at 60–90 fps.

## Architecture

```
User Input → Memory & Context → Dialogue FSM → LLM (Personality-aware)
                                                      ↓
                                               Intent Router
                                                      ↓
                         ┌────────────────────────────┼──────────────────────────┐
                         ↓                            ↓                          ↓
                   Emotion Model              Gesture Engine                Spatial AI
                   (VAD + Arc)          (Single + Choreography)        (Gaze, Proximity)
                         ↓                            ↓                          ↓
                  Micro-Expressions             Personality                 Arc Tracker
                  (Advanced + Leakage)          Modifiers                  (Rapport, Momentum)
                         ↓                            ↓                          ↓
                         └────────────────────────────┼──────────────────────────┘
                                                      ↓
                                             Voice Engine (Piper TTS)
                                             + Viseme Generation
                                                      ↓
                                               WebSocket Bridge
                                                      ↓
                                  Three.js + VRM Avatar (60-90 fps)
                                  + Breathing System + Performance Monitor
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

## Phase 1-3: Core Systems

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

## Phase 4: Advanced Behavior & Context Intelligence

### Conversation Memory (`server/memory/context.py`)
Sliding-window conversation memory with:
- **Recent turns** — full detail for LLM context
- **Topic tracking** — what subjects have been discussed (work, family, health, etc.)
- **User fact extraction** — remembers name, preferences, favorites from natural conversation
- **Automatic summarization** — compresses older turns to stay within context limits

### Emotional Arc Tracker (`server/emotion/arc.py`)
Models how emotion evolves over the conversation:
- **Valence/arousal momentum** — is the conversation trending happier, sadder, calmer?
- **Rapport level** — 0-1 scale of conversational connection, grows with turns and positive emotion
- **Emotional volatility** — detects unstable emotional states
- **Recovery detection** — knows when user is coming back from something difficult
- **Behavior modifiers** — automatically adjusts gesture intensity, spatial comfort, gaze intimacy based on arc

### Gesture Choreography (`server/gesture/choreography.py`)
Multi-gesture sequences instead of isolated single gestures:
- **Greeting choreography** — wave → tilt_head → open_hands
- **Empathy choreography** — tilt_head → lean_forward → nod
- **Thinking choreography** — chin_rest → tilt_head → nod
- **Excitement choreography** — lean_forward → open_hands → nod
- **Farewell choreography** — nod → wave → lean_back
- Cooldown system prevents overuse; sequences scale with rapport

### Dialogue State Machine (`server/dialogue/state_machine.py`)
Models the conversational flow through states:
- `idle` → `greeting` → `small_talk` → `engaged` → `emotional` → `farewell`
- Each state applies behavior modifiers (gesture scale, distance bias, gaze preference, tone)
- Transitions driven by user content, emotion, silence duration, turn count, rapport

### Personality System (`server/personality/traits.py`)
Configurable avatar personas using Big Five personality traits:
- **Openness** → curiosity, initiative, contemplative pauses
- **Conscientiousness** → speaking pace, precision
- **Extraversion** → gesture frequency/amplitude, preferred distance, approach willingness
- **Agreeableness** → eye contact duration, mirroring strength, expression intensity
- **Neuroticism** → emotional reactivity, gaze aversion rate

**Presets:**
| Name | Style | Key Traits |
|------|-------|-----------|
| `eve` | Warm, empathetic companion | High agreeableness, moderate extraversion |
| `spark` | Energetic, playful | Very high extraversion, high openness |
| `sage` | Calm, thoughtful | High openness, low extraversion, low neuroticism |
| `whisper` | Shy, gentle | Low extraversion, high agreeableness, moderate neuroticism |

## Phase 5: Production Polish & Advanced Systems

### Performance Monitor (`client/src/performance/monitor.ts`)
Adaptive quality system that maintains framerate:
- Tracks frame time with rolling average, detects drops
- Three quality levels: `high`, `medium`, `low`
- Auto-downgrades on sustained drops, slowly recovers
- Controls: shadow resolution, saccades, micro-expressions, gesture count, pixel ratio

### Advanced Micro-Expression Engine (`server/emotion/microexpressions.py`)
Goes beyond basic emotion→blend shape mapping:
- **Emotional leakage** — suppressed previous emotions briefly flash through
- **Reactive expressions** — responds to user keywords (compliment → smile, bad news → empathy frown)
- **Blended expressions** — bittersweet (sad + slight smile), nervous excitement, skeptical interest
- **Asymmetric expressions** — one-sided smirks, single brow raises for natural variety

### Breathing & Autonomic Simulation (`client/src/avatar/breathing.ts`)
Physiologically-grounded breathing that responds to emotion:
- **Breath rate** — 12 bpm (calm) to 24 bpm (aroused), smooth transitions
- **Breath depth** — deeper when calm, shallow when anxious
- **Sighs** — triggered by emotional relief or sadness
- **Breath holds** — on surprise or concentration
- **Heart rate estimation** — drives subtle body micro-sway
- Applies to chest, shoulder, spine bones with subtle intensity

### Multi-Modal Input Processor (`server/input/processor.py`)
Aggregates signals beyond text:
- Voice activity events (user starts/stops speaking)
- Proximity change events (user moves closer/farther)
- Attention tracking (user looks at/away from avatar)
- Gesture detection (user hand gestures via tracking)
- Computes unified engagement score (0-1) and triggers reactive behavior

### Session Analytics (`server/analytics/telemetry.py`)
Tracks behavior metrics for tuning:
- Emotion distribution per session
- Gesture usage frequency
- Gaze pattern statistics
- Dialogue state transition history
- Turn timing and processing latency
- Peak and final rapport levels
- Exportable as JSON for analysis

## Configuration

Edit `.env` or set environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BASE_URL` | `http://localhost:1234/v1` | OpenAI-compatible LLM endpoint |
| `LLM_MODEL` | `gemma-3-12b-it` | Model name |
| `PIPER_ENABLED` | `true` | Enable/disable TTS |
| `TRACKING_MODE` | `webxr` | `webxr`, `webcam`, or `manual` |
| `DEFAULT_DISTANCE` | `1.5` | Default conversational distance (meters) |
| `PERSONALITY` | `eve` | Avatar personality: `eve`, `spark`, `sage`, `whisper` |
| `MEMORY_MAX_RECENT_TURNS` | `30` | Max conversation turns kept in full detail |
| `TELEMETRY_ENABLED` | `true` | Enable session analytics |
| `TELEMETRY_EXPORT_PATH` | _(empty)_ | Path to export session JSON on disconnect |

## Project Structure

```
server/
├── main.py                     # WebSocket orchestrator (Phase 1-5 pipeline)
├── config.py                   # Pydantic Settings
├── protocol.py                 # Message types & parsing
├── llm/
│   ├── client.py              # OpenAI-compatible LLM streaming
│   └── prompts.py             # Context-aware system prompts
├── intent/
│   ├── schema.py              # Core data types (AvatarIntent, Emotion, etc.)
│   └── router.py              # LLM response parsing
├── memory/
│   └── context.py             # Conversation memory & user fact extraction
├── emotion/
│   ├── model.py               # VAD keyword analysis
│   ├── arc.py                 # Emotional arc tracker (rapport, momentum)
│   └── microexpressions.py    # Advanced micro-expression generation
├── gesture/
│   ├── engine.py              # Single gesture selection
│   └── choreography.py        # Multi-gesture choreography sequences
├── dialogue/
│   └── state_machine.py       # Dialogue FSM (idle→greeting→engaged→farewell)
├── personality/
│   └── traits.py              # Big Five personality system + presets
├── spatial/
│   ├── anchor.py              # User position tracking
│   ├── gaze.py                # Gaze computation
│   └── proximity.py           # Proxemic zones
├── voice/
│   ├── tts.py                 # Piper TTS wrapper
│   └── viseme.py              # Grapheme-to-viseme mapping
├── input/
│   └── processor.py           # Multi-modal input processing
└── analytics/
    └── telemetry.py           # Session metrics & export

client/src/
├── main.ts                     # Entry point (Phase 1-5 wiring)
├── connection.ts               # WebSocket client
├── avatar/
│   ├── loader.ts              # VRM loading
│   ├── controller.ts          # Master orchestrator (Phase 1-5)
│   ├── blendshapes.ts         # Facial expressions
│   ├── gaze.ts                # Eye/head tracking
│   ├── posture.ts             # Body pose + gestures
│   ├── lipsync.ts             # Viseme interpolation
│   └── breathing.ts           # Autonomic breathing simulation
├── animation/
│   ├── loop.ts                # 60fps requestAnimationFrame
│   ├── transitions.ts         # Easing functions & damping
│   └── blender.ts             # Multi-layer animation blending
├── spatial/
│   ├── positioning.ts         # World-space movement
│   └── behaviors.ts           # Mirror behavior
├── performance/
│   └── monitor.ts             # Adaptive quality system
└── scene/
    ├── setup.ts               # Three.js initialization
    └── environment.ts         # Scene environment
```
