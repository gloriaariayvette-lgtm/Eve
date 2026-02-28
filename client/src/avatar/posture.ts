/**
 * Posture controller — body pose driven by emotion + idle animation.
 *
 * Handles:
 * - Idle breathing (chest/shoulder rise-fall)
 * - Weight shifting (subtle side-to-side sway)
 * - Emotion-driven posture changes (slouch, stand tall, lean)
 * - Gesture playback (nod, shrug, lean, wave, etc.)
 */

import * as THREE from 'three';
import { VRM } from '@pixiv/three-vrm';
import { damp, easeOutCubic } from '../animation/transitions';

export interface GestureCmd {
  gesture: string;
  intensity: number;
  duration: number;
  delay: number;
}

// Emotion → posture offsets (spine rotation in radians)
const EMOTION_POSTURE: Record<string, { spineX: number; spineZ: number; shoulderY: number }> = {
  neutral:    { spineX: 0,      spineZ: 0,     shoulderY: 0 },
  joy:        { spineX: -0.03,  spineZ: 0,     shoulderY: -0.02 },   // slightly upright
  sadness:    { spineX: 0.06,   spineZ: 0,     shoulderY: 0.03 },    // slouched
  anger:      { spineX: -0.04,  spineZ: 0,     shoulderY: 0.02 },    // tense, forward
  surprise:   { spineX: -0.05,  spineZ: 0,     shoulderY: -0.02 },   // lean back
  fear:       { spineX: 0.04,   spineZ: 0.02,  shoulderY: 0.04 },    // shrink
  interest:   { spineX: -0.03,  spineZ: 0,     shoulderY: 0 },       // lean forward
  tenderness: { spineX: -0.02,  spineZ: 0.01,  shoulderY: -0.01 },   // gentle tilt
  disgust:    { spineX: -0.02,  spineZ: -0.02, shoulderY: 0.02 },    // slight recoil
  contempt:   { spineX: -0.01,  spineZ: -0.02, shoulderY: 0 },       // slight lean back
};

interface ActiveGesture {
  gesture: string;
  intensity: number;
  startTime: number;
  duration: number;
  progress: number;
}

export class PostureController {
  private vrm: VRM | null = null;
  private idleTime = 0;

  // Current posture state (smooth values)
  private spineX = 0;
  private spineZ = 0;
  private shoulderY = 0;
  private targetSpineX = 0;
  private targetSpineZ = 0;
  private targetShoulderY = 0;

  // Active gestures
  private activeGestures: ActiveGesture[] = [];
  private gestureTime = 0;

  // Velaris: posture stability from EmoClaw groundedness (0=fidgety, 1=steady)
  private stability = 0.7;

  setVRM(vrm: VRM): void {
    this.vrm = vrm;
  }

  /**
   * Velaris: Set posture stability from EmoClaw groundedness.
   * Higher stability = less idle sway, more controlled movements.
   */
  setStability(value: number): void {
    this.stability = Math.max(0, Math.min(1, value));
  }

  /**
   * Set target emotion for posture.
   */
  setEmotion(primary: string, arousal: number): void {
    const posture = EMOTION_POSTURE[primary] ?? EMOTION_POSTURE.neutral;
    const scale = 0.5 + arousal * 0.5; // more pronounced at high arousal
    this.targetSpineX = posture.spineX * scale;
    this.targetSpineZ = posture.spineZ * scale;
    this.targetShoulderY = posture.shoulderY * scale;
  }

  /**
   * Play a gesture.
   */
  playGesture(cmd: GestureCmd): void {
    setTimeout(() => {
      this.activeGestures.push({
        gesture: cmd.gesture,
        intensity: cmd.intensity,
        startTime: this.gestureTime,
        duration: cmd.duration,
        progress: 0,
      });
    }, cmd.delay * 1000);
  }

  /**
   * Update posture. Call every frame.
   */
  update(dt: number): void {
    if (!this.vrm) return;

    this.idleTime += dt;
    this.gestureTime += dt;

    // Smooth posture transitions
    this.spineX = damp(this.spineX, this.targetSpineX, 3, dt);
    this.spineZ = damp(this.spineZ, this.targetSpineZ, 3, dt);
    this.shoulderY = damp(this.shoulderY, this.targetShoulderY, 3, dt);

    // Idle breathing
    const breathCycle = Math.sin(this.idleTime * 1.2) * 0.008;
    const breathPhase = Math.sin(this.idleTime * 1.2 + 0.5) * 0.003;

    // Idle weight shift (very subtle sway, reduced by stability)
    const swayScale = 1.0 - this.stability * 0.6; // high stability = less sway
    const sway = (Math.sin(this.idleTime * 0.3) * 0.004 + Math.sin(this.idleTime * 0.7) * 0.002) * swayScale;

    // Apply to bones
    const spine = this.vrm.humanoid?.getNormalizedBoneNode('spine');
    const chest = this.vrm.humanoid?.getNormalizedBoneNode('chest');
    const leftShoulder = this.vrm.humanoid?.getNormalizedBoneNode('leftShoulder');
    const rightShoulder = this.vrm.humanoid?.getNormalizedBoneNode('rightShoulder');
    const hips = this.vrm.humanoid?.getNormalizedBoneNode('hips');
    const head = this.vrm.humanoid?.getNormalizedBoneNode('head');
    const neck = this.vrm.humanoid?.getNormalizedBoneNode('neck');

    if (spine) {
      spine.rotation.x = this.spineX + breathCycle;
      spine.rotation.z = this.spineZ + sway;
    }

    if (chest) {
      chest.rotation.x = breathPhase;
    }

    if (leftShoulder) {
      leftShoulder.rotation.z = this.shoulderY + breathCycle * 0.5;
    }
    if (rightShoulder) {
      rightShoulder.rotation.z = -(this.shoulderY + breathCycle * 0.5);
    }

    if (hips) {
      hips.rotation.z = sway * 0.5;
    }

    // Process active gestures
    this._updateGestures(dt, head, neck, spine, leftShoulder, rightShoulder);
  }

  private _updateGestures(
    dt: number,
    head: THREE.Object3D | null,
    neck: THREE.Object3D | null,
    spine: THREE.Object3D | null,
    leftShoulder: THREE.Object3D | null,
    rightShoulder: THREE.Object3D | null,
  ): void {
    const finished: number[] = [];

    for (let i = 0; i < this.activeGestures.length; i++) {
      const g = this.activeGestures[i];
      g.progress = (this.gestureTime - g.startTime) / g.duration;

      if (g.progress >= 1.0) {
        finished.push(i);
        continue;
      }

      // Bell curve: ramp up then down
      const envelope = Math.sin(g.progress * Math.PI) * g.intensity;

      this._applyGestureFrame(g.gesture, envelope, head, neck, spine, leftShoulder, rightShoulder);
    }

    // Remove finished gestures (reverse order)
    for (let i = finished.length - 1; i >= 0; i--) {
      this.activeGestures.splice(finished[i], 1);
    }
  }

  private _applyGestureFrame(
    gesture: string,
    envelope: number,
    head: THREE.Object3D | null,
    neck: THREE.Object3D | null,
    spine: THREE.Object3D | null,
    leftShoulder: THREE.Object3D | null,
    rightShoulder: THREE.Object3D | null,
  ): void {
    switch (gesture) {
      case 'nod':
        if (head) head.rotation.x += Math.sin(envelope * Math.PI * 3) * 0.08 * envelope;
        break;

      case 'shake_head':
        if (head) head.rotation.y += Math.sin(envelope * Math.PI * 4) * 0.1 * envelope;
        break;

      case 'shrug':
        if (leftShoulder) leftShoulder.rotation.z += 0.15 * envelope;
        if (rightShoulder) rightShoulder.rotation.z -= 0.15 * envelope;
        if (head) head.rotation.z += 0.03 * envelope;
        break;

      case 'lean_forward':
        if (spine) spine.rotation.x -= 0.08 * envelope;
        break;

      case 'lean_back':
        if (spine) spine.rotation.x += 0.06 * envelope;
        break;

      case 'tilt_head':
        if (head) head.rotation.z += 0.1 * envelope;
        break;

      case 'open_hands':
        // Subtle shoulder opening
        if (leftShoulder) leftShoulder.rotation.y -= 0.05 * envelope;
        if (rightShoulder) rightShoulder.rotation.y += 0.05 * envelope;
        break;

      case 'arms_crossed':
        if (leftShoulder) {
          leftShoulder.rotation.z += 0.1 * envelope;
          leftShoulder.rotation.y += 0.1 * envelope;
        }
        if (rightShoulder) {
          rightShoulder.rotation.z -= 0.1 * envelope;
          rightShoulder.rotation.y -= 0.1 * envelope;
        }
        break;

      case 'chin_rest':
        if (head) {
          head.rotation.x += 0.04 * envelope;
          head.rotation.z += 0.05 * envelope;
        }
        break;

      case 'wave':
        if (rightShoulder) {
          rightShoulder.rotation.z -= 0.3 * envelope;
          rightShoulder.rotation.x += Math.sin(envelope * Math.PI * 3) * 0.15;
        }
        break;
    }
  }
}
