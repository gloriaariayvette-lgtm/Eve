/**
 * Eve Avatar Engine — Client Entry Point
 *
 * Initializes:
 * 1. Three.js scene with cinematic lighting
 * 2. VRM avatar (loaded from server or placeholder)
 * 3. WebSocket connection to Eve server
 * 4. 60fps animation loop driving all avatar subsystems
 * 5. UI for text input and status display
 */

import { createScene } from './scene/setup';
import { AvatarLoader } from './avatar/loader';
import { AvatarController } from './avatar/controller';
import { AnimationLoop } from './animation/loop';
import { Connection, ServerMessage } from './connection';
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
    // Try loading a VRM model from the models directory
    statusEl.textContent = 'loading avatar...';
    const vrm = await avatarLoader.load('/models/default.vrm');
    scene.add(vrm.scene);
    controller.setVRM(vrm);
    console.log('[Main] VRM avatar loaded');
  } catch (e) {
    console.warn('[Main] No VRM model found, using placeholder:', e);
    const placeholder = avatarLoader.createPlaceholder();
    scene.add(placeholder);
    // Controller won't have VRM — subsystems degrade gracefully
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

    // Auto-hide after estimated duration
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

// --- WebXR Tracking (PSVR2 / SteamVR) ---

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
    // WebXR session would be initialized here when user enters VR mode
    // For now, tracking data comes through the standard WebSocket
  } catch (e) {
    console.log('[WebXR] Check failed:', e);
  }
}

// --- Animation Loop ---

animLoop.onUpdate((dt, elapsed) => {
  // Update avatar subsystems
  controller.update(dt);

  // Render
  renderer.render(scene, camera);

  // Update FPS display
  fpsEl.textContent = `${animLoop.fps} fps`;
});

// --- Start Everything ---

async function init(): Promise<void> {
  console.log('[Eve] Avatar Engine initializing...');

  await loadAvatar();
  initWebXR();
  connection.connect();
  animLoop.start();

  console.log('[Eve] Ready');
}

init();
