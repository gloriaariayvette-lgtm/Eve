/**
 * Breathing & autonomic nervous system simulation.
 *
 * Simulates realistic breathing patterns that respond to emotional state:
 * - Base breathing rate (12-20 breaths/min at rest)
 * - Arousal-linked rate increase (up to 25 breaths/min when excited/anxious)
 * - Sighs triggered by emotional relief or sadness
 * - Breath holds during surprise or concentration
 * - Subtle chest/shoulder/abdomen motion driven by breath phase
 *
 * Also simulates:
 * - Heart rate estimation (affects subtle body sway)
 * - Autonomic flush (not visual, but affects arousal decay rate)
 */

import * as THREE from 'three';
import { VRM } from '@pixiv/three-vrm';
import { damp } from '../animation/transitions';

export interface BreathState {
  phase: number;          // 0-1, 0=start of inhale, 0.4=peak, 1=end of exhale
  rate: number;           // breaths per minute
  depth: number;          // 0-1, how deep the breath is
  isSighing: boolean;
  isHolding: boolean;
  heartRate: number;      // bpm estimate
}

export interface EmotionInput {
  arousal: number;
  valence: number;
  primary: string;
}

export class BreathingSystem {
  private vrm: VRM | null = null;

  // Breath cycle
  private phase = 0;             // 0-1 cycle
  private currentRate = 14;       // breaths/min
  private targetRate = 14;
  private currentDepth = 0.5;
  private targetDepth = 0.5;

  // Autonomic state
  private heartRate = 72;
  private targetHeartRate = 72;
  private arousalLevel = 0.2;

  // Sigh/hold state
  private isSighing = false;
  private sighTimer = 0;
  private sighCooldown = 0;
  private isHolding = false;
  private holdTimer = 0;

  // Noise for natural variation
  private noisePhase = Math.random() * Math.PI * 2;

  setVRM(vrm: VRM): void {
    this.vrm = vrm;
  }

  /**
   * Update emotional state inputs.
   */
  setEmotion(emotion: EmotionInput): void {
    this.arousalLevel = emotion.arousal;

    // Breathing rate: 12 (calm) to 24 (very aroused)
    this.targetRate = 12 + emotion.arousal * 12;

    // Depth: deeper when calm, shallower when anxious
    if (emotion.primary === 'fear' || emotion.primary === 'anger') {
      this.targetDepth = 0.3 + emotion.arousal * 0.3; // shallow, rapid
    } else if (emotion.primary === 'sadness') {
      this.targetDepth = 0.6 + emotion.arousal * 0.2; // deeper, slower sighs
    } else {
      this.targetDepth = 0.4 + (1 - emotion.arousal) * 0.3; // normal range
    }

    // Heart rate: 65 (calm) to 110 (very aroused)
    this.targetHeartRate = 65 + emotion.arousal * 45;

    // Trigger sigh on emotional relief (valence going positive, moderate arousal)
    if (emotion.valence > 0.3 && emotion.arousal < 0.5 && this.sighCooldown <= 0) {
      if (Math.random() < 0.15) {
        this.triggerSigh();
      }
    }

    // Trigger sigh on sadness
    if (emotion.primary === 'sadness' && emotion.arousal > 0.3 && this.sighCooldown <= 0) {
      if (Math.random() < 0.2) {
        this.triggerSigh();
      }
    }

    // Breath hold on surprise
    if (emotion.primary === 'surprise' && emotion.arousal > 0.6) {
      this.triggerHold(0.5 + Math.random() * 0.5);
    }
  }

  /**
   * Trigger a sigh (deep breath + slow exhale).
   */
  triggerSigh(): void {
    if (this.isSighing || this.sighCooldown > 0) return;
    this.isSighing = true;
    this.sighTimer = 0;
    this.sighCooldown = 8; // minimum 8 seconds between sighs
  }

  /**
   * Trigger a breath hold.
   */
  triggerHold(duration: number): void {
    if (this.isHolding) return;
    this.isHolding = true;
    this.holdTimer = duration;
  }

  /**
   * Alias for triggerHold — used by Velaris event handler.
   */
  triggerBreathHold(duration: number): void {
    this.triggerHold(duration);
  }

  /**
   * Velaris: Set breathing modifiers from EmoClaw state.
   * Rate modifier: 1.0 = normal, >1 = faster, <1 = slower.
   * Depth modifier: 1.0 = normal, >1 = deeper, <1 = shallower.
   */
  setModifiers(rateModifier: number, depthModifier: number): void {
    this.targetRate = 14 * rateModifier;
    this.targetDepth = 0.5 * depthModifier;
  }

  /**
   * Get current breath state for external systems.
   */
  getState(): BreathState {
    return {
      phase: this.phase,
      rate: Math.round(this.currentRate),
      depth: this.currentDepth,
      isSighing: this.isSighing,
      isHolding: this.isHolding,
      heartRate: Math.round(this.heartRate),
    };
  }

  /**
   * Update breathing system. Call every frame.
   */
  update(dt: number): void {
    if (!this.vrm) return;

    // Smooth rate and depth transitions
    this.currentRate = damp(this.currentRate, this.targetRate, 2, dt);
    this.currentDepth = damp(this.currentDepth, this.targetDepth, 3, dt);
    this.heartRate = damp(this.heartRate, this.targetHeartRate, 1.5, dt);

    // Cooldowns
    if (this.sighCooldown > 0) this.sighCooldown -= dt;

    // Noise for natural variation
    this.noisePhase += dt * 0.7;
    const breathNoise = Math.sin(this.noisePhase) * 0.05;

    // Handle breath hold
    if (this.isHolding) {
      this.holdTimer -= dt;
      if (this.holdTimer <= 0) {
        this.isHolding = false;
      }
      // During hold, phase doesn't advance, slight tension
      this._applyBreathBones(0.35, this.currentDepth * 1.2, dt);
      return;
    }

    // Handle sigh
    if (this.isSighing) {
      this.sighTimer += dt;
      const sighDuration = 3.0; // 3-second sigh cycle
      const sighPhase = this.sighTimer / sighDuration;

      if (sighPhase >= 1.0) {
        this.isSighing = false;
      } else {
        // Deep inhale (0-0.3), hold (0.3-0.4), slow exhale (0.4-1.0)
        let breathValue: number;
        if (sighPhase < 0.3) {
          breathValue = sighPhase / 0.3; // ramp up
        } else if (sighPhase < 0.4) {
          breathValue = 1.0; // hold at peak
        } else {
          breathValue = 1.0 - (sighPhase - 0.4) / 0.6; // slow exhale
        }
        this._applyBreathBones(breathValue * 0.5, this.currentDepth * 1.5, dt);
        return;
      }
    }

    // Normal breathing cycle
    const cycleSpeed = this.currentRate / 60; // cycles per second
    this.phase += dt * cycleSpeed;
    if (this.phase >= 1.0) this.phase -= 1.0;

    // Breath curve: inhale (0-0.4), exhale (0.4-1.0), with natural asymmetry
    let breathValue: number;
    if (this.phase < 0.4) {
      // Inhale — slightly faster
      breathValue = Math.sin((this.phase / 0.4) * Math.PI * 0.5);
    } else {
      // Exhale — slightly slower, more relaxed
      breathValue = Math.cos(((this.phase - 0.4) / 0.6) * Math.PI * 0.5);
    }

    breathValue += breathNoise;

    this._applyBreathBones(breathValue, this.currentDepth, dt);
  }

  /**
   * Apply breathing motion to VRM bones.
   */
  private _applyBreathBones(breathValue: number, depth: number, dt: number): void {
    if (!this.vrm?.humanoid) return;

    const spine = this.vrm.humanoid.getNormalizedBoneNode('spine');
    const chest = this.vrm.humanoid.getNormalizedBoneNode('chest');
    const leftShoulder = this.vrm.humanoid.getNormalizedBoneNode('leftShoulder');
    const rightShoulder = this.vrm.humanoid.getNormalizedBoneNode('rightShoulder');

    const intensity = depth * 0.012; // subtle!

    // Chest expansion
    if (chest) {
      chest.rotation.x += breathValue * intensity * -0.5;
    }

    // Shoulder rise on inhale
    const shoulderLift = breathValue * intensity * 0.3;
    if (leftShoulder) {
      leftShoulder.rotation.z += shoulderLift;
    }
    if (rightShoulder) {
      rightShoulder.rotation.z -= shoulderLift;
    }

    // Subtle spine extension on inhale
    if (spine) {
      spine.rotation.x += breathValue * intensity * -0.3;
    }

    // Heart rate → subtle body micro-sway
    const swayFreq = this.heartRate / 60; // Hz
    const sway = Math.sin(performance.now() / 1000 * swayFreq * Math.PI * 2) * 0.001 * this.arousalLevel;
    if (spine) {
      spine.rotation.z += sway;
    }
  }
}
