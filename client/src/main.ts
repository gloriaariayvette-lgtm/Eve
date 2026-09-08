/**
 * Eve Avatar Engine — Client Entry Point
 *
 * Phase 6: Velaris Integration
 * - Velaris event reactions (kiss, anti-kiss, unprecedented, etc.)
 * - EmoClaw behavior modifiers → breathing, posture, gaze tuning
 * - Emotional color → environment lighting
 * - WebXR session lifecycle for PSVR2/SteamVR
 * - VR environment with Velaris-influenced atmosphere
 */

import * as THREE from 'three';
import { createScene } from './scene/setup';
import { addEnvironment, updateEnvironmentColor, updateEnvironmentFrame } from './scene/environment';
import { AvatarLoader } from './avatar/loader';
import {
  AvatarController,
  ArcStateData,
  BehaviorModifiersData,
  DialogueStateData,
  VelarisEventData,
} from './avatar/controller';
import { AnimationLoop } from './animation/loop';
import { Connection, ServerMessage } from './connection';
import { PerformanceMonitor, AdaptiveQuality } from './performance/monitor';
import type { VisemeData } from './avatar/lipsync';

// --- DOM Elements ---
const canvas = document.getElementById('canvas') as HTMLCanvasElement;
const statusEl = document.getElementById('status')!;
const speechBubble = document.getElementById('speech-bubble')!;
const userInput = document.getElementById('user-input') as HTMLInputElement;
const sendBtn = document.getElementById('send-btn')!;
const fpsEl = document.getElementById('fps')!;
const emotionDebug = document.getElementById('emotion-debug')!;
const gazeDebug = document.getElementById('gaze-debug')!;

// --- Initialize Systems ---
const { scene, camera, renderer, clock } = createScene(canvas);
const avatarLoader = new AvatarLoader();
const controller = new AvatarController();
const animLoop = new AnimationLoop();
const connection = new Connection();

// Performance monitoring
const perfMonitor = new PerformanceMonitor();
const quality = new AdaptiveQuality(perfMonitor);

// Add environment and wire up emotional color
addEnvironment(scene);
controller.onEmotionalColorChange((color: string) => {
  updateEnvironmentColor(scene, color);
});

// --- Audio Playback ---
let audioContext: AudioContext | null = null;

function getAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new AudioContext();
  }
  return audioContext;
}

async function playAudioB64(b64: string, sampleRate: number): Promise<void> {
  try {
    const ctx = getAudioContext();
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }

    const audioBuffer = await ctx.decodeAudioData(bytes.buffer);
    const source = ctx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(ctx.destination);
    source.start(0);
  } catch (e) {
    console.error('[Audio] Playback failed:', e);
  }
}

// --- Load Avatar ---
async function loadAvatar(): Promise<void> {
  try {
    statusEl.textContent = 'loading avatar...';
    const vrm = await avatarLoader.load('/models/default.vrm');
    scene.add(vrm.scene);
    controller.setVRM(vrm);
    console.log('[Main] VRM avatar loaded');
  } catch (e) {
    console.warn('[Main] No VRM model found, using placeholder:', e);
    const placeholder = avatarLoader.createPlaceholder();
    scene.add(placeholder);
  }
}

// --- WebSocket Message Handlers ---

connection.on('_connected', () => {
  statusEl.textContent = 'connected';
  statusEl.className = 'connected';
});

connection.on('_disconnected', () => {
  statusEl.textContent = 'disconnected';
  statusEl.className = '';
});

connection.on('status', (msg: ServerMessage) => {
  const status = msg.data.status as string;
  statusEl.textContent = status;
  statusEl.className = status;
});

connection.on('avatar_intent', (msg: ServerMessage) => {
  controller.handleIntent(msg.data);

  // Show speech text
  const speechText = msg.data.speechText as string;
  if (speechText) {
    speechBubble.textContent = speechText;
    speechBubble.classList.add('visible');

    const words = speechText.split(' ').length;
    const displayTime = Math.max(3000, words * 400);
    setTimeout(() => {
      speechBubble.classList.remove('visible');
    }, displayTime);
  }

  // Update debug display
  const emotion = msg.data.emotion as Record<string, unknown> | undefined;
  if (emotion) {
    emotionDebug.textContent = `emotion: ${emotion.primary} (v:${(emotion.valence as number)?.toFixed(2)} a:${(emotion.arousal as number)?.toFixed(2)})`;
  }

  const gaze = msg.data.gaze as Record<string, unknown> | undefined;
  if (gaze) {
    gazeDebug.textContent = `gaze: ${gaze.target}`;
  }
});

connection.on('viseme_sequence', (msg: ServerMessage) => {
  const visemes = msg.data.visemes as VisemeData[];
  if (visemes) {
    controller.handleVisemes(visemes);
  }
});

connection.on('speech_audio', (msg: ServerMessage) => {
  const audio = msg.data.audio as string;
  const sampleRate = msg.data.sampleRate as number;
  if (audio) {
    playAudioB64(audio, sampleRate);
  }
});

connection.on('speech_start', (msg: ServerMessage) => {
  statusEl.textContent = 'speaking';
  statusEl.className = 'speaking';
});

connection.on('speech_end', () => {
  controller.handleSpeechEnd();
  statusEl.textContent = 'connected';
  statusEl.className = 'connected';
});

// Dialogue state changes (standalone mode)
connection.on('dialogue_state', (msg: ServerMessage) => {
  const stateData = msg.data as unknown as DialogueStateData;
  controller.handleDialogueState(stateData);
  console.log('[Main] Dialogue state:', stateData.state);
});

// Emotional arc updates
connection.on('arc_state', (msg: ServerMessage) => {
  const arcData = msg.data as unknown as ArcStateData;
  controller.handleArcState(arcData);

  const debug = controller.getDebugInfo();
  const debugEl = document.getElementById('arc-debug');
  if (debugEl) {
    debugEl.textContent = `rapport:${debug.rapport} mood:${debug.dominant} color:${debug.color}`;
  }
});

// Session metrics
connection.on('session_metrics', (msg: ServerMessage) => {
  console.log('[Telemetry] Session metrics:', msg.data);
});

// --- Velaris-specific message handlers ---

// Emotional color (environment lighting)
connection.on('emotional_color', (msg: ServerMessage) => {
  const color = msg.data.color as string;
  if (color) {
    controller.handleEmotionalColor(color);
    console.log('[Velaris] Emotional color:', color);
  }
});

// EmoClaw behavior modifiers
connection.on('behavior_modifiers', (msg: ServerMessage) => {
  const modifiers = msg.data as unknown as BehaviorModifiersData;
  controller.handleBehaviorModifiers(modifiers);
});

// Velaris events (kiss, anti-kiss, unprecedented, etc.)
connection.on('velaris_event', (msg: ServerMessage) => {
  const eventData = msg.data as unknown as VelarisEventData;
  controller.handleVelarisEvent(eventData);
  console.log('[Velaris] Event:', eventData.eventType);

  // Flash event type on status
  const prevStatus = statusEl.textContent;
  statusEl.textContent = `event: ${eventData.eventType}`;
  statusEl.className = 'event';
  setTimeout(() => {
    statusEl.textContent = prevStatus || 'connected';
    statusEl.className = 'connected';
  }, 2000);
});

// --- User Input ---

function sendMessage(): void {
  const text = userInput.value.trim();
  if (!text) return;

  // Resume audio context on user interaction
  audioContext?.resume();

  connection.sendUserInput(text);
  userInput.value = '';

  statusEl.textContent = 'thinking';
  statusEl.className = 'thinking';
}

userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    sendMessage();
  }
});

sendBtn.addEventListener('click', sendMessage);

// --- WebXR Session Lifecycle (PSVR2 / SteamVR) ---

let xrSession: XRSession | null = null;
let xrRefSpace: XRReferenceSpace | null = null;

async function initWebXR(): Promise<void> {
  if (!navigator.xr) {
    console.log('[WebXR] Not available, using default positions');
    return;
  }

  try {
    const supported = await navigator.xr.isSessionSupported('immersive-vr');
    if (!supported) {
      console.log('[WebXR] Immersive VR not supported');
      return;
    }

    console.log('[WebXR] VR session available — PSVR2/SteamVR detected');

    // Create Enter VR button
    const vrBtn = document.createElement('button');
    vrBtn.id = 'vr-btn';
    vrBtn.textContent = 'Enter VR';
    vrBtn.style.cssText = `
      position: fixed; bottom: 20px; right: 20px; z-index: 1000;
      padding: 12px 24px; font-size: 16px; font-weight: bold;
      background: #cc4280; color: white; border: none; border-radius: 8px;
      cursor: pointer; font-family: monospace;
    `;
    vrBtn.addEventListener('click', () => toggleVRSession());
    document.body.appendChild(vrBtn);
  } catch (e) {
    console.log('[WebXR] Check failed:', e);
  }
}

async function toggleVRSession(): Promise<void> {
  if (xrSession) {
    await xrSession.end();
    return;
  }

  try {
    // Request immersive-vr with hand tracking (PSVR2 Sense controllers)
    xrSession = await navigator.xr!.requestSession('immersive-vr', {
      requiredFeatures: ['local-floor'],
      optionalFeatures: ['hand-tracking', 'bounded-floor'],
    });

    xrSession.addEventListener('end', () => {
      xrSession = null;
      xrRefSpace = null;
      renderer.xr.enabled = false;
      animLoop.start(); // resume normal animation loop

      const btn = document.getElementById('vr-btn');
      if (btn) btn.textContent = 'Enter VR';
      console.log('[WebXR] VR session ended');
    });

    // Set up reference space
    xrRefSpace = await xrSession.requestReferenceSpace('local-floor');

    // Configure renderer for XR
    renderer.xr.enabled = true;
    await renderer.xr.setSession(xrSession);

    // Stop regular animation loop — XR has its own
    animLoop.stop();

    // XR render loop
    renderer.xr.setAnimationLoop((time: number, frame: XRFrame | undefined) => {
      const dt = clock.getDelta();

      if (frame && xrRefSpace) {
        // Extract head pose
        const viewerPose = frame.getViewerPose(xrRefSpace);
        if (viewerPose) {
          const pos = viewerPose.transform.position;
          const headPos = { x: pos.x, y: pos.y, z: pos.z };

          // Send tracking data to server
          const trackingData: Record<string, unknown> = {
            headPosition: headPos,
          };

          // Try to get hand positions (PSVR2 Sense controllers)
          for (const inputSource of xrSession!.inputSources) {
            if (inputSource.gripSpace) {
              const gripPose = frame.getPose(inputSource.gripSpace, xrRefSpace!);
              if (gripPose) {
                const gp = gripPose.transform.position;
                if (inputSource.handedness === 'left') {
                  trackingData.leftHandPosition = { x: gp.x, y: gp.y, z: gp.z };
                } else if (inputSource.handedness === 'right') {
                  trackingData.rightHandPosition = { x: gp.x, y: gp.y, z: gp.z };
                }
              }
            }
          }

          connection.sendTracking(trackingData);
          controller.updateTracking({
            headPosition: headPos,
            headRotation: { x: 0, y: 0, z: 0 },
          });
        }
      }

      // Update avatar
      controller.update(dt);

      // Performance monitoring
      const frameStart = performance.now();
      renderer.render(scene, camera);
      const frameTime = performance.now() - frameStart;
      perfMonitor.recordFrame(frameTime);
    });

    const btn = document.getElementById('vr-btn');
    if (btn) btn.textContent = 'Exit VR';
    console.log('[WebXR] VR session started');

  } catch (e) {
    console.error('[WebXR] Failed to start VR session:', e);
    xrSession = null;
  }
}

// --- Animation Loop (non-VR) ---

animLoop.onUpdate((dt, elapsed) => {
  const frameStart = performance.now();

  // Update avatar subsystems
  controller.update(dt);

  // Update environment color transitions
  updateEnvironmentFrame(dt);

  // Render
  renderer.render(scene, camera);

  // Performance monitoring
  const frameTime = performance.now() - frameStart;
  perfMonitor.recordFrame(frameTime);
  perfMonitor.evaluate(elapsed);

  // Update FPS display with quality indicator
  const snap = perfMonitor.getSnapshot();
  // AdaptiveQuality exposes the derived settings; the level itself lives on
  // the monitor's snapshot.
  const qualityIndicator = snap.qualityLevel === 'high' ? '' : ` [${snap.qualityLevel}]`;
  fpsEl.textContent = `${animLoop.fps} fps${qualityIndicator}`;
});

// --- Start Everything ---

async function init(): Promise<void> {
  console.log('[Eve] Avatar Engine initializing (Phase 6 — Velaris Integration)...');

  await loadAvatar();
  initWebXR();
  connection.connect();
  animLoop.start();

  console.log('[Eve] Ready — Velaris body engine active');
  console.log('[Eve] Systems: EmoClaw bridge, gesture choreography, micro-expressions, breathing, spatial');
  console.log('[Eve] WebXR: PSVR2/SteamVR session lifecycle ready');
}

init();
