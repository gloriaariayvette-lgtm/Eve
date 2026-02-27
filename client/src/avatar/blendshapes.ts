/**
 * Facial expression blend shape driver.
 *
 * Drives VRM expression presets (happy, sad, angry, surprised, etc.)
 * and individual blend shapes for micro-expressions.
 *
 * Handles:
 * - Primary emotion → VRM expression preset
 * - Micro-expression overlays (brow, nose, lip corners)
 * - Idle subtle movements (breathing affect on face, micro-twitches)
 * - Smooth transitions between emotional states
 */

import { VRM } from '@pixiv/three-vrm';
import { AnimationBlender } from '../animation/blender';
import { damp } from '../animation/transitions';

// VRM preset expression names
const VRM_EXPRESSIONS = ['happy', 'angry', 'sad', 'relaxed', 'surprised', 'neutral'] as const;

// Map from server emotion names to VRM expression presets
const EMOTION_TO_VRM: Record<string, string> = {
  joy: 'happy',
  sadness: 'sad',
  anger: 'angry',
  surprise: 'surprised',
  fear: 'surprised',    // VRM doesn't have fear, use surprised + blend shapes
  disgust: 'angry',     // approximate
  contempt: 'neutral',
  interest: 'relaxed',
  tenderness: 'relaxed',
  neutral: 'neutral',
};

export interface EmotionState {
  primary: string;
  valence: number;
  arousal: number;
  dominance: number;
}

export interface MicroExpressionCmd {
  blendShape: string;
  weight: number;
  duration: number;
  delay: number;
}

export class BlendShapeDriver {
  private vrm: VRM | null = null;
  private blender = new AnimationBlender();
  private currentEmotion: EmotionState = {
    primary: 'neutral',
    valence: 0,
    arousal: 0.2,
    dominance: 0.5,
  };
  private idleTime = 0;

  setVRM(vrm: VRM): void {
    this.vrm = vrm;
  }

  /**
   * Set the target emotion state. Transitions happen smoothly.
   */
  setEmotion(emotion: EmotionState): void {
    // Clear previous emotion expression
    const prevVrmExpr = EMOTION_TO_VRM[this.currentEmotion.primary] ?? 'neutral';
    if (prevVrmExpr !== 'neutral') {
      this.blender.setTarget(`expr_${prevVrmExpr}`, 0, { smoothing: 4 });
    }

    this.currentEmotion = emotion;

    // Set new emotion expression
    const vrmExpr = EMOTION_TO_VRM[emotion.primary] ?? 'neutral';
    if (vrmExpr !== 'neutral') {
      // Intensity scales with arousal
      const intensity = 0.3 + emotion.arousal * 0.5;
      this.blender.setTarget(`expr_${vrmExpr}`, intensity, { smoothing: 5 });
    }
  }

  /**
   * Apply micro-expression overlays.
   */
  applyMicroExpressions(micros: MicroExpressionCmd[]): void {
    for (const micro of micros) {
      const key = `micro_${micro.blendShape}`;
      // Delayed start, auto-expire
      setTimeout(() => {
        this.blender.setTarget(key, micro.weight, {
          smoothing: 12,
          duration: micro.duration,
        });
      }, micro.delay * 1000);
    }
  }

  /**
   * Update blend shapes. Call every frame.
   */
  update(dt: number): void {
    if (!this.vrm?.expressionManager) return;

    this.idleTime += dt;

    // Update blender
    const weights = this.blender.update(dt);

    // Apply VRM expression presets
    for (const exprName of VRM_EXPRESSIONS) {
      const key = `expr_${exprName}`;
      const weight = weights.get(key) ?? 0;
      this.vrm.expressionManager.setValue(exprName, weight);
    }

    // Apply idle micro-movements (subtle, constant life)
    this._applyIdleSubtleties(dt);

    // Apply micro-expression blend shapes directly if supported
    for (const [key, weight] of weights) {
      if (key.startsWith('micro_')) {
        const shapeName = key.slice(6); // remove 'micro_' prefix
        try {
          this.vrm.expressionManager.setValue(shapeName, weight);
        } catch {
          // Blend shape might not exist on this model
        }
      }
    }

    // Update VRM expression manager
    this.vrm.expressionManager.update();
  }

  /**
   * Idle subtle facial movements — makes the avatar look alive.
   */
  private _applyIdleSubtleties(dt: number): void {
    if (!this.vrm?.expressionManager) return;

    // Subtle brow micro-movement
    const browNoise = Math.sin(this.idleTime * 0.7) * 0.02 + Math.sin(this.idleTime * 1.3) * 0.01;

    // Slight mouth corner movement (micro-smile oscillation)
    const mouthNoise = Math.sin(this.idleTime * 0.5) * 0.01;

    // Apply as very subtle overlay (these won't conflict with expressions
    // since they're so small)
    try {
      // Using relaxed expression for subtle smile
      const currentRelaxed = this.blender.getValue('expr_relaxed');
      if (currentRelaxed < 0.1) {
        this.vrm.expressionManager.setValue('relaxed', Math.max(0, mouthNoise + 0.02));
      }
    } catch {
      // Model might not support all expressions
    }
  }
}
