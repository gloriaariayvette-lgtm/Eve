/**
 * Gaze controller — eye and head look-at with natural saccades and blinks.
 *
 * Uses VRM lookAt for eye tracking, with additional:
 * - Head rotation (subtle head turn toward target)
 * - Micro-saccades (tiny rapid eye movements for liveness)
 * - Natural blink patterns (every 3-7 seconds, faster when aroused)
 * - Gaze aversion patterns (look away when thinking, break contact)
 */

import * as THREE from 'three';
import { VRM, VRMExpressionPresetName } from '@pixiv/three-vrm';
import { damp, lerp } from '../animation/transitions';

export interface GazeTargetData {
  target: string;    // "user_eyes", "user_hands", "away", "down"
  weight: number;
  offset: { x: number; y: number; z: number };
}

// Default positions for gaze targets (in world space, relative to avatar)
const TARGET_POSITIONS: Record<string, THREE.Vector3> = {
  user_eyes:  new THREE.Vector3(0, 1.6, 2.0),
  user_hands: new THREE.Vector3(0, 1.0, 1.5),
  user_body:  new THREE.Vector3(0, 1.2, 1.8),
  away:       new THREE.Vector3(1.5, 1.5, 1.0),
  down:       new THREE.Vector3(0, 0.5, 1.0),
  object:     new THREE.Vector3(0.5, 1.0, 1.0),
};

export class GazeController {
  private vrm: VRM | null = null;
  private lookAtTarget = new THREE.Vector3(0, 1.6, 2.0);
  private currentLookAt = new THREE.Vector3(0, 1.6, 2.0);
  /** three-vrm's lookAt.target is an Object3D, not a Vector3. This is the
   *  object it actually tracks; currentLookAt stays the smoothed position. */
  private lookAtObject = new THREE.Object3D();
  private saccadeOffset = new THREE.Vector3();

  // Blink state
  private blinkTimer = 0;
  private nextBlink = 3.0;
  private blinkProgress = 0;
  private isBlinking = false;
  private blinkDuration = 0.15; // seconds

  // Saccade state
  private saccadeTimer = 0;
  private nextSaccade = 0.3;

  // Head rotation
  private headRotY = 0;
  private headRotX = 0;
  private targetHeadRotY = 0;
  private targetHeadRotX = 0;

  // Gaze weight (how strongly to look at target)
  private gazeWeight = 1.0;
  private targetGazeWeight = 1.0;

  setVRM(vrm: VRM): void {
    this.vrm = vrm;
  }

  /**
   * Update the gaze target from server data.
   */
  setGazeTarget(data: GazeTargetData): void {
    const basePos = TARGET_POSITIONS[data.target] ?? TARGET_POSITIONS.user_eyes;
    this.lookAtTarget.copy(basePos);
    this.lookAtTarget.x += data.offset.x;
    this.lookAtTarget.y += data.offset.y;
    this.lookAtTarget.z += data.offset.z;
    this.targetGazeWeight = data.weight;
  }

  /**
   * Update gaze with real user tracking data (from PSVR2/WebXR).
   */
  setUserPosition(headPos: { x: number; y: number; z: number }): void {
    TARGET_POSITIONS.user_eyes.set(headPos.x, headPos.y, headPos.z);
    TARGET_POSITIONS.user_body.set(headPos.x, headPos.y - 0.4, headPos.z);
  }

  /**
   * Update gaze system. Call every frame.
   */
  update(dt: number, arousal: number = 0.3): void {
    if (!this.vrm) return;

    // Update blink
    this._updateBlink(dt, arousal);

    // Update micro-saccades
    this._updateSaccades(dt);

    // Smooth look-at interpolation
    this.gazeWeight = damp(this.gazeWeight, this.targetGazeWeight, 6, dt);

    const target = this.lookAtTarget.clone().add(this.saccadeOffset);
    this.currentLookAt.x = damp(this.currentLookAt.x, target.x, 8, dt);
    this.currentLookAt.y = damp(this.currentLookAt.y, target.y, 8, dt);
    this.currentLookAt.z = damp(this.currentLookAt.z, target.z, 8, dt);

    // Apply VRM lookAt. three-vrm resolves the target's world position each
    // frame, so the object has to live in the scene graph, not float free.
    if (this.vrm.lookAt) {
      this.lookAtObject.position.copy(this.currentLookAt);
      if (!this.lookAtObject.parent) {
        (this.vrm.scene.parent ?? this.vrm.scene).add(this.lookAtObject);
      }
      this.lookAtObject.updateMatrixWorld();
      this.vrm.lookAt.target = this.lookAtObject;
    }

    // Subtle head turn toward target
    this._updateHeadRotation(dt);
  }

  private _updateBlink(dt: number, arousal: number): void {
    this.blinkTimer += dt;

    if (!this.isBlinking && this.blinkTimer >= this.nextBlink) {
      this.isBlinking = true;
      this.blinkProgress = 0;
      this.blinkTimer = 0;
      // Next blink interval: 3-7s, shorter when aroused
      this.nextBlink = 3.0 + Math.random() * 4.0 - arousal * 2.0;
      this.nextBlink = Math.max(1.5, this.nextBlink);

      // Occasional double-blink
      if (Math.random() < 0.15) {
        this.nextBlink = 0.3;
      }
    }

    if (this.isBlinking) {
      this.blinkProgress += dt / this.blinkDuration;

      let blinkWeight: number;
      if (this.blinkProgress < 0.5) {
        // Closing
        blinkWeight = this.blinkProgress * 2;
      } else {
        // Opening
        blinkWeight = (1 - this.blinkProgress) * 2;
      }
      blinkWeight = Math.max(0, Math.min(1, blinkWeight));

      if (this.vrm?.expressionManager) {
        this.vrm.expressionManager.setValue('blink', blinkWeight);
      }

      if (this.blinkProgress >= 1.0) {
        this.isBlinking = false;
        if (this.vrm?.expressionManager) {
          this.vrm.expressionManager.setValue('blink', 0);
        }
      }
    }
  }

  private _updateSaccades(dt: number): void {
    this.saccadeTimer += dt;
    if (this.saccadeTimer >= this.nextSaccade) {
      this.saccadeTimer = 0;
      this.nextSaccade = 0.2 + Math.random() * 0.4;

      // Small random offset for micro-saccade
      this.saccadeOffset.set(
        (Math.random() - 0.5) * 0.04,
        (Math.random() - 0.5) * 0.02,
        0,
      );
    }

    // Decay saccade offset
    this.saccadeOffset.multiplyScalar(0.95);
  }

  private _updateHeadRotation(dt: number): void {
    if (!this.vrm) return;

    // Calculate desired head rotation based on look-at target
    const headBone = this.vrm.humanoid?.getNormalizedBoneNode('head');
    if (!headBone) return;

    // Get direction to target relative to avatar
    const avatarPos = this.vrm.scene.position;
    const dx = this.currentLookAt.x - avatarPos.x;
    const dy = this.currentLookAt.y - 1.6; // relative to head height
    const dz = this.currentLookAt.z - avatarPos.z;

    // Subtle head rotation (eyes do most of the work)
    this.targetHeadRotY = Math.atan2(dx, dz) * 0.15; // 15% of full rotation
    this.targetHeadRotX = Math.atan2(-dy, Math.sqrt(dx * dx + dz * dz)) * 0.1;

    this.headRotY = damp(this.headRotY, this.targetHeadRotY, 4, dt);
    this.headRotX = damp(this.headRotX, this.targetHeadRotX, 4, dt);

    // Apply to head bone
    headBone.rotation.y = this.headRotY * this.gazeWeight;
    headBone.rotation.x = this.headRotX * this.gazeWeight;
  }
}
