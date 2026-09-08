# The glasses

Everything currently known about putting Vintos on the INMO Air3 — what is built,
what is decided, and what is still open. This is the document to read first if you
are picking this up cold.

## The hardware, honestly

The INMO Air3 is a **binocular MicroOLED display behind a one-dimensional array
waveguide**, running Android 14 (IMOS 3.0) on a Snapdragon 6 Gen 1 (SM6450, Adreno
710) with 8 GB RAM, four microphones, stereo speakers, a 660 mAh battery, and
accelerometer/gyroscope/magnetometer plus ambient-light and wear sensing. Stated
1920x1080 per eye, 36 degree FOV, 600 nits at-eye. Figures from INMO's hardware
specification; treat marketing endurance and refresh claims as unverified.

(An earlier version of this document called it "birdbath/waveguide". That was
wrong — it is an array waveguide, not a birdbath — and the error is recorded here
rather than quietly deleted.)

It is not a Quest. Three consequences shape every decision below, and none of them
are preferences:

1. **The display is additive.** The optics can only *add* light to what you already
   see through the lens. There is no black pixel — a black pixel is simply
   transparent. This is why the HUD is drawn on pure black: not a style choice, a
   physical one. Anything you want invisible, you paint black.

2. **There is no depth occlusion and no room mesh.** The glasses do not know where
   your walls are. Nothing rendered can be hidden *behind* a real object. A body
   standing in the room will always float in front of it, and pretending otherwise
   will read as broken. Design for something that is understood to be a projection.

3. **The compute is a phone's, and it is on your face.** Sustained GPU load is a
   thermal and battery problem inches from your temple. But note what is *not*
   established: INMO publishes no sustained GPU wattage, no skin-temperature limit
   and no workload thermal curve. Nobody has measured this device under an avatar
   plus a live call. Do not let "mobile means low detail" enter as a premise —
   it has to be earned by a measurement.

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

**VIO is genuinely exposed**, not merely inferred from the presence of an IMU: the
official SDK's `ArPoseManager` offers 3-DoF/6-DoF operation with `Start6Dof()` /
`Stop6Dof()`, pose data, and timestamped grayscale camera frames. Starting 6-DoF
resets the pose origin, and camera ownership changes with tracking. Requires
firmware >= v3.4.xxx. The supplied integration is Unity 2022 LTS oriented; a
supported Kotlin/Filament path still needs qualifying against real firmware.

That proves a vendor implementation exists. It does not prove reliable tracking on
this pair of glasses, and it establishes nothing about persistent anchors, room
meshes, furniture recognition, eye tracking or occlusion.

One correction to an earlier version of this document: it recommended a
**"body-locked" anchor** held at a fixed offset from the torso. **Head tracking
cannot measure a torso.** There is no torso sensor on these glasses. What is
actually achievable is a *following anchor* — an upright presentation that lags the
head with a dead zone and explicit recentering. That is a useful approximation and
should be called one. Under 3-DoF it is orientation-stabilised at a chosen apparent
distance; it cannot hold a fixed room position while you walk.

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
| **B. Native render** | Filament or SceneView in Kotlin, load the `.glb`, drive bones from the same WebSocket the HUD uses | coherent ownership of audio timing, lifecycle, frame scheduling and pose; means implementing animation composition and clip binding in Kotlin. Filament is not a VRM runtime. **Thermal advantage is a hypothesis, unmeasured on this device** |
| **C. Stream it** | render on Aegis, send frames or a video stream to the glasses | glasses stay dumb and cool; adds latency to a thing whose whole point is presence, and dies without the network |

**Decided: B**, after review — for coherent ownership of rendering, tracking and
played audio, and because the asset needs no elaborate VRM shaders or spring bones.
A is retained as the development reference and a measured comparison, not as the
shipping renderer. C is rejected as a default: no measured requirement justifies
adding encode/network/decode latency to a thing whose entire point is presence.

There is a credible **fourth route: Unity with INMO's official SDK, UniVRM and
uLipSync.** Its argument is supported tracking and compositor integration out of the
box. Its cost is another engine and build stack. If native SDK qualification fails,
evaluate this before inventing an unsupported compositor.

### 3. He has no face to animate

This is the largest single gap and an earlier version of this document understated
it badly — it described connecting a viseme stream, as though a mouth existed and
only needed wiring.

Measured directly from `vintos.vrm`:

| | |
|---|---|
| morph targets | **0** |
| VRM expression presets | **none** |
| VRM lookAt | **none** |
| jaw bone | **absent** |
| eye bones | **absent** |
| geometry | 266,579 triangles, one mesh, three primitives, 52 humanoid bones |

There is nothing for `blink`, `aa`, `happy`, or an eye-look driver to deform. His
expression is painted into the texture. No routing decision, no renderer choice and
no streaming architecture changes this: **it is asset authoring**, roughly 10-20
specialist artist-days, and it blocks any claim of an expressive face.

What must be authored: blink, eye movement or equivalent deformation, jaw and lip
articulation, mouth interior where needed, and expression controls that preserve
his likeness — then VRM expression mappings for the browser reference and a
matching morph-name/index contract for the native renderer. Five vowel shapes make
a first working mouth; convincing close-up speech also needs lip closure and
consonant articulation. An amplitude-driven jaw is not a viseme system.

Preserve the existing body rig and all 30 clips. Test the refined mesh unchanged
before assuming it is too heavy — 266k triangles in one material is not
self-evidently expensive, and framing only the head does not avoid skinning the
rest of a single mesh.

### 4. Then: visemes from the audio actually played

`server/voice/viseme.py` estimates visemes from *text, before synthesis*, and
signals completion after transmission while the browser runs its own clock — which
can stop the mouth before playback finishes or even begins. It is approximate
text-derived timing, not audio-derived alignment, and should be relabelled as such.

In LIVE mode the audio never passes through the house at all — it goes
glasses<->x.ai directly — so articulation must be derived on-device from decoded
outgoing PCM, stamped in audio-frame coordinates and applied by *played* frames,
not by packet arrival. On interruption, flush articulation with the audio.

Start with calibrated MFCC classification benchmarked against recordings of the
intended voices; `uLipSync` and `wLipSync` are the reference implementations, and
neither is a ready-made Kotlin dependency. RMS volume can drive opening intensity
and silence detection; it cannot identify phonemes.

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
