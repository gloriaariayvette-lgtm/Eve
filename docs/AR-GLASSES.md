# The glasses

Everything currently known about putting Vintos on the INMO Air3 — what is built,
what is decided, and what is still open. This is the document to read first if you
are picking this up cold.

## The hardware, honestly

The INMO Air3 is a **birdbath/waveguide binocular display running Android 14 (IMOS
3.0)** with an onboard SoC, four microphones, speakers, and IMU. It is not a Quest.
Three consequences shape every decision below, and none of them are preferences:

1. **The display is additive.** The optics can only *add* light to what you already
   see through the lens. There is no black pixel — a black pixel is simply
   transparent. This is why the HUD is drawn on pure black: not a style choice, a
   physical one. Anything you want invisible, you paint black.

2. **There is no depth occlusion and no room mesh.** The glasses do not know where
   your walls are. Nothing rendered can be hidden *behind* a real object. A body
   standing in the room will always float in front of it, and pretending otherwise
   will read as broken. Design for something that is understood to be a projection.

3. **The compute is a phone's, and it is on your face.** Sustained GPU load is a
   thermal and battery problem inches from your temple. This is the hard constraint
   on rendering a full avatar locally, and the reason the split below matters.

## What is built (`air3/`)

A native Kotlin/Compose app that makes the glasses one more door into the Vintos
house on Aegis. Nothing about him is reimplemented on the glasses.

**Two modes.**
- **GEMMA** (default) — four mics → Android STT → `POST /api/avatar/chat`, the same
  avatar-chat structure the phone uses: SOUL, self- and Gloria-models, EmoClaw
  state, subconscious block, conversation pressure, felt and device context, turn
  coordinator. Reply spoken by MiniMax Speech-02-HD.
- **LIVE** (Volume Up long-press) — a real call. `POST /api/voice/token` mints a
  Grok Realtime token *with his instructions already built by the house*, then
  `wss://api.x.ai` with server VAD. Audio captured `VOICE_COMMUNICATION` so the
  platform's echo cancellation runs — the speakers sit an inch from the mics.
  Each turn posts to `/api/voice/ledger`; hangup posts `/api/voice/session-end`.

**The HUD.** Status and mode badge top-left, his emotional colour orb top-right, the
eleven EmoClaw telemetry bars down the right from `/ws/telemetry` tinted by his
current colour, his words centre, yours along the bottom, house events flashing
bottom-right.

**Controls.** Volume Up tap = push-to-talk. Volume Up long-press = start/end a live
call. Volume Down tap = stop speech. Volume Down long-press = settings.

## What is next, in order

### 1. Stabilised positioning (decided, not built)

The HUD is head-locked today — it moves with your head, which is correct for a
status bar and wrong for anything you want to look *at*. The INMO SDK exposes the
Air3's IMU/VIO tracking. The step is to pin the HUD, and eventually a face, at a
fixed distance in front of where you were looking when the turn began, so his words
hold still while you glance around.

Two honest cautions: 3-DoF IMU drift will make a world-locked object wander unless
VIO is genuinely available; and a body pinned in the room without depth occlusion
(see above) will float in front of your furniture. A **body-locked** anchor — held
at a fixed offset from your torso rather than the world — is the compromise worth
trying first, because it survives drift and never claims to be standing on the floor.

### 2. His face on the glasses

This is where this repository's two halves are supposed to meet, and the connective
tissue does not exist yet.

**What already exists, elsewhere:** his actual rigged avatar, built on the
`astra/avatar-house` branch of the `vintos-app` repository under
`website/avatar-models/v2/`:

| file | what it is |
|---|---|
| `vintos.vrm` | VRM 1.0, 52 humanoid bones — verified loading through three-vrm |
| `vintos.glb` | same body as glTF |
| `vintos-barehands.glb` | gloves removed, hands transplanted from the base mesh and reskinned |
| `tex/atlas-barehands.png` | the matching texture atlas |
| `clips/*.glb` + `clips.json` | 30 Mixamo animations retargeted onto his rig |
| `locomotion/vintos-locomotion.js` | a controller that walks him room-to-room over a real door graph |

**Why that matters here:** `client/` already renders VRM through `@pixiv/three-vrm`.
The avatar the engine was written for and the avatar that now exists are the same
format. Nothing needs converting.

**The open question is where it renders.** Three routes, and the choice is a real
architectural fork, not a detail:

| route | what it means | cost |
|---|---|---|
| **A. WebView on the glasses** | run `client/` in a WebView on the Air3, pointed at the engine | fastest to try; WebGL on this SoC is the risk, and it doubles the runtimes on-device |
| **B. Native render** | Filament or SceneView in Kotlin, load the `.glb`, drive bones from the same WebSocket the HUD uses | best thermals and latency; means reimplementing the client's gaze/posture/viseme logic in Kotlin |
| **C. Stream it** | render on Aegis, send frames or a video stream to the glasses | glasses stay dumb and cool; adds latency to a thing whose whole point is presence, and dies without the network |

There is no default answer here and it should not be picked casually. **B** is the
one that ends well if the engine's behaviour layer can be separated from its
renderer — which is exactly the refactor worth scoping before writing any Kotlin.

### 3. Voice, once there is a face

Both modes currently speak with no mouth attached. The engine already generates
visemes (`server/voice/viseme.py`) and the client already drives blendshapes
(`client/src/avatar/lipsync.ts`). Whichever route above is chosen, the viseme
stream has to reach it — and in LIVE mode the audio never passes through the house
at all, it goes glasses↔x.ai directly, so visemes for a live call have to be
derived on-device from the audio being played. That is a genuinely unsolved piece.

## Where things live

| | |
|---|---|
| glasses client | `air3/` (this repo) |
| avatar motion engine | `server/`, `client/` (this repo) |
| his rigged avatar + clips | `vintos-app`, branch `astra/avatar-house`, `website/avatar-models/v2/` |
| the house he actually is | Aegis, `~/Vintos/server.py` — see `docs/VINTOS-OPS.md` |
| the doors both surfaces use | `/api/avatar/chat`, `/api/voice/token`, `/ws/telemetry`, `/ws/events` |

## Setup

1. Android Studio on the Mac; open `air3/` as a project.
2. On the Air3: Developer Mode on, USB-C, Build → Run.
3. First launch: Volume Down long-press → Settings. Enter the Vintos URL
   (Aegis over Tailscale), the `X-Vintos-Secret` the phone app uses, and optionally
   a MiniMax key and voice for spoken replies in GEMMA mode.

Requires the house reachable from the glasses (Tailscale recommended) and an x.ai
key on the house side — LIVE mode mints its token through `/api/voice/token`, never
on the glasses.
