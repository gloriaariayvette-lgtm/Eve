/**
 * Spatial behaviors — high-level movement patterns for the avatar.
 *
 * Mirror: lean when the user leans (from tracking data)
 * Conversational: maintain appropriate distance
 * Dynamic: circle, approach, retreat, sit, stand, kneel
 */

import * as THREE from 'three';
import { VRM } from '@pixiv/three-vrm';
import { damp } from '../animation/transitions';

export interface TrackingData {
  headPosition: { x: number; y: number; z: number };
  headRotation: { x: number; y: number; z: number };
  leftHandPosition?: { x: number; y: number; z: number };
  rightHandPosition?: { x: number; y: number; z: number };
}

export class SpatialBehaviors {
  private vrm: VRM | null = null;

  // Mirror state
  private mirrorLeanX = 0;
  private mirrorLeanZ = 0;
  private mirrorEnabled = true;

  setVRM(vrm: VRM): void {
    this.vrm = vrm;
  }

  /**
   * Update mirroring behavior based on user tracking data.
   */
  updateMirror(tracking: TrackingData, dt: number): void {
    if (!this.vrm || !this.mirrorEnabled) return;

    // Mirror the user's head tilt/lean
    // Invert X rotation (lean) so the avatar mirrors the user
    const userLeanX = tracking.headRotation.x * 0.3; // scale down
    const userLeanZ = -tracking.headRotation.z * 0.3; // mirror Z axis

    this.mirrorLeanX = damp(this.mirrorLeanX, userLeanX, 3, dt);
    this.mirrorLeanZ = damp(this.mirrorLeanZ, userLeanZ, 3, dt);

    // Apply to spine as subtle lean
    const spine = this.vrm.humanoid?.getNormalizedBoneNode('spine');
    if (spine) {
      spine.rotation.x += this.mirrorLeanX;
      spine.rotation.z += this.mirrorLeanZ;
    }
  }

  /**
   * Check if user is gesturing (hands raised above waist).
   */
  isUserGesturing(tracking: TrackingData): boolean {
    const headY = tracking.headPosition.y;
    const waistY = headY - 0.5;

    if (tracking.leftHandPosition && tracking.leftHandPosition.y > waistY) return true;
    if (tracking.rightHandPosition && tracking.rightHandPosition.y > waistY) return true;
    return false;
  }

  setMirrorEnabled(enabled: boolean): void {
    this.mirrorEnabled = enabled;
  }
}
