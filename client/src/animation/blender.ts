/**
 * Multi-layer animation blending system.
 *
 * Layers (applied bottom to top):
 *   1. Idle (breathing, weight shift) — always active, low weight
 *   2. Posture (emotion-driven body pose) — smooth transitions
 *   3. Gesture (active gesture overlay) — time-limited
 *   4. Face (blend shape expressions) — multiple active simultaneously
 *   5. Gaze (eye/head look-at) — highest priority, always tracking
 *   6. Lip sync (viseme shapes) — overrides mouth blend shapes during speech
 */

import { SmoothValue, damp } from './transitions';

export interface BlendTarget {
  name: string;
  weight: number;       // target weight 0-1
  current: number;      // current interpolated weight
  smoothing: number;    // transition speed
  expiresAt: number;    // 0 = persistent, >0 = auto-remove after this time
}

export class AnimationBlender {
  private targets = new Map<string, BlendTarget>();
  private time: number = 0;

  /**
   * Set a blend target. If it already exists, update its target weight.
   */
  setTarget(
    name: string,
    weight: number,
    options: {
      smoothing?: number;
      duration?: number;  // auto-expire after N seconds
      immediate?: boolean;
    } = {},
  ): void {
    const existing = this.targets.get(name);
    const smoothing = options.smoothing ?? 8;
    const expiresAt = options.duration ? this.time + options.duration : 0;

    if (existing) {
      existing.weight = weight;
      existing.smoothing = smoothing;
      if (expiresAt > 0) existing.expiresAt = expiresAt;
      if (options.immediate) existing.current = weight;
    } else {
      this.targets.set(name, {
        name,
        weight,
        current: options.immediate ? weight : 0,
        smoothing,
        expiresAt,
      });
    }
  }

  /**
   * Remove a blend target (with smooth fade-out).
   */
  removeTarget(name: string): void {
    const target = this.targets.get(name);
    if (target) {
      target.weight = 0;
      target.expiresAt = this.time + 0.5; // fade out over 0.5s then remove
    }
  }

  /**
   * Update all blend targets. Call once per frame.
   * Returns map of name → current interpolated weight.
   */
  update(dt: number): Map<string, number> {
    this.time += dt;
    const result = new Map<string, number>();
    const toRemove: string[] = [];

    for (const [name, target] of this.targets) {
      // Check expiration
      if (target.expiresAt > 0 && this.time > target.expiresAt) {
        target.weight = 0;
      }

      // Interpolate
      target.current = damp(target.current, target.weight, target.smoothing, dt);

      // Remove if fully faded and expired
      if (target.expiresAt > 0 && target.current < 0.001 && target.weight === 0) {
        toRemove.push(name);
        continue;
      }

      if (target.current > 0.001) {
        result.set(name, target.current);
      }
    }

    for (const name of toRemove) {
      this.targets.delete(name);
    }

    return result;
  }

  /**
   * Get current value of a specific target.
   */
  getValue(name: string): number {
    return this.targets.get(name)?.current ?? 0;
  }

  /**
   * Clear all targets.
   */
  clear(): void {
    this.targets.clear();
  }
}
