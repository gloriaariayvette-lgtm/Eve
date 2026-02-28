/**
 * Avatar world-space positioning — handles movement and distance.
 */

import * as THREE from 'three';
import { VRM } from '@pixiv/three-vrm';
import { damp } from '../animation/transitions';

export interface SpatialCmd {
  action: string;
  targetDistance: number;
  speed: number;
  targetPosition?: { x: number; y: number; z: number };
}

export class AvatarPositioning {
  private vrm: VRM | null = null;
  private currentPos = new THREE.Vector3(0, 0, 0);
  private targetPos = new THREE.Vector3(0, 0, 0);
  private moveSpeed = 0.5;

  // For circle behavior
  private circleAngle = 0;
  private isCircling = false;

  setVRM(vrm: VRM): void {
    this.vrm = vrm;
  }

  /**
   * Apply a spatial command from the server.
   */
  applyCommand(cmd: SpatialCmd, userPosition: THREE.Vector3): void {
    this.moveSpeed = cmd.speed;

    switch (cmd.action) {
      case 'approach':
      case 'retreat': {
        // Move toward/away from user along the line between avatar and user
        const dir = new THREE.Vector3().subVectors(userPosition, this.currentPos).normalize();
        this.targetPos.copy(userPosition).sub(dir.multiplyScalar(cmd.targetDistance));
        this.targetPos.y = 0; // stay on ground
        this.isCircling = false;
        break;
      }

      case 'circle':
        this.isCircling = true;
        break;

      case 'sit':
        this.targetPos.y = -0.4; // lower avatar
        this.isCircling = false;
        break;

      case 'stand':
        this.targetPos.y = 0;
        this.isCircling = false;
        break;

      case 'kneel':
        this.targetPos.y = -0.6;
        this.isCircling = false;
        break;

      case 'hold':
        this.isCircling = false;
        break;
    }

    if (cmd.targetPosition) {
      this.targetPos.set(cmd.targetPosition.x, cmd.targetPosition.y, cmd.targetPosition.z);
    }
  }

  /**
   * Velaris: Apply a distance impulse (move closer or further from user).
   * Negative = move closer, positive = move away.
   */
  applyDistanceImpulse(impulse: number, userPosition: THREE.Vector3): void {
    const dir = new THREE.Vector3().subVectors(userPosition, this.currentPos).normalize();
    const currentDist = this.currentPos.distanceTo(userPosition);
    const newDist = Math.max(0.5, currentDist - impulse); // negative impulse = closer
    this.targetPos.copy(userPosition).sub(dir.multiplyScalar(newDist));
    this.targetPos.y = this.currentPos.y;
    this.isCircling = false;
  }

  /**
   * Update positioning. Call every frame.
   */
  update(dt: number, userPosition: THREE.Vector3): void {
    if (!this.vrm) return;

    // Circle behavior
    if (this.isCircling) {
      this.circleAngle += dt * this.moveSpeed * 0.5;
      const radius = this.currentPos.distanceTo(userPosition) || 1.5;
      this.targetPos.x = userPosition.x + Math.sin(this.circleAngle) * radius;
      this.targetPos.z = userPosition.z + Math.cos(this.circleAngle) * radius;
      this.targetPos.y = 0;
    }

    // Smooth movement
    this.currentPos.x = damp(this.currentPos.x, this.targetPos.x, this.moveSpeed * 3, dt);
    this.currentPos.y = damp(this.currentPos.y, this.targetPos.y, this.moveSpeed * 3, dt);
    this.currentPos.z = damp(this.currentPos.z, this.targetPos.z, this.moveSpeed * 3, dt);

    // Apply to VRM scene
    this.vrm.scene.position.copy(this.currentPos);

    // Face toward user
    const lookDir = new THREE.Vector3().subVectors(userPosition, this.currentPos);
    lookDir.y = 0;
    if (lookDir.length() > 0.01) {
      const targetAngle = Math.atan2(lookDir.x, lookDir.z);
      const currentAngle = this.vrm.scene.rotation.y - Math.PI; // VRM faces -Z
      const angleDiff = targetAngle - currentAngle;
      this.vrm.scene.rotation.y = Math.PI + damp(currentAngle, targetAngle, 3, dt);
    }
  }
}
