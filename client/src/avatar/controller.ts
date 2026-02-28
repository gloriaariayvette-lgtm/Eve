/**
 * Master avatar controller — orchestrates all avatar subsystems.
 *
 * Receives commands from the WebSocket connection and routes them
 * to the appropriate subsystem (blendshapes, gaze, posture, lipsync, spatial).
 * Updates all systems each frame.
 *
 * Phase 6 (Velaris integration):
 * - Velaris event reactions (kiss, anti-kiss, unprecedented, etc.)
 * - EmoClaw behavior modifiers (gesture frequency, gaze warmth, posture stability)
 * - Emotional color for environment lighting
 * - Breathing modifiers from EmoClaw arousal/tension
 */

import * as THREE from 'three';
import { VRM } from '@pixiv/three-vrm';
import { BlendShapeDriver, EmotionState, MicroExpressionCmd } from './blendshapes';
import { GazeController, GazeTargetData } from './gaze';
import { PostureController, GestureCmd } from './posture';
import { LipSyncDriver, VisemeData } from './lipsync';
import { BreathingSystem, EmotionInput } from './breathing';
import { AvatarPositioning, SpatialCmd } from '../spatial/positioning';
import { SpatialBehaviors, TrackingData } from '../spatial/behaviors';

export interface ArcStateData {
  rapport: number;
  valenceMomentum: number;
  dominantEmotion: string;
  isRecovering: boolean;
}

export interface DialogueStateData {
  state: string;
  modifiers?: {
    gestureScale?: number;
    distanceBias?: number;
    toneHint?: string;
  };
}

export interface BehaviorModifiersData {
  gestureFrequency: number;
  gestureAmplitude: number;
  gesturePlayfulness: number;
  preferredDistance: number;
  approachWillingness: number;
  shouldLeanForward: boolean;
  postureStability: number;
  eyeContactIntensity: number;
  gazeCuriosity: number;
  gazeWarmth: number;
  expressionDepth: number;
  warmthOverlay: number;
  tensionOverlay: number;
  breathRateModifier: number;
  breathDepthModifier: number;
  emotionalColor: string;
}

export interface VelarisEventData {
  eventType: string;
  gestures: GestureCmd[];
  microExpressions: MicroExpressionCmd[];
  gazeOverride: string | null;
  gazeOverrideDuration: number;
  triggerSigh: boolean;
  triggerBreathHold: number;
  distanceImpulse: number;
}

export class AvatarController {
  readonly blendShapes = new BlendShapeDriver();
  readonly gaze = new GazeController();
  readonly posture = new PostureController();
  readonly lipSync = new LipSyncDriver();
  readonly positioning = new AvatarPositioning();
  readonly behaviors = new SpatialBehaviors();
  readonly breathing = new BreathingSystem();

  private vrm: VRM | null = null;
  private currentEmotion: EmotionState = {
    primary: 'neutral',
    valence: 0,
    arousal: 0.2,
    dominance: 0.5,
  };

  // User position for spatial calculations
  private userPosition = new THREE.Vector3(0, 0, 2.0);

  // Dialogue and arc state
  private dialogueState: string = 'idle';
  private arcState: ArcStateData = {
    rapport: 0.2,
    valenceMomentum: 0,
    dominantEmotion: 'neutral',
    isRecovering: false,
  };

  // Velaris: EmoClaw behavior modifiers
  private behaviorModifiers: BehaviorModifiersData | null = null;

  // Velaris: Emotional color for environment
  private _emotionalColor: string = '#cc4280';

  // Velaris: Gaze override (from events)
  private gazeOverrideTarget: string | null = null;
  private gazeOverrideTimer: number = 0;

  // Callback for emotional color changes (scene lighting)
  private _onColorChange: ((color: string) => void) | null = null;

  /**
   * Initialize with a loaded VRM model.
   */
  setVRM(vrm: VRM): void {
    this.vrm = vrm;
    this.blendShapes.setVRM(vrm);
    this.gaze.setVRM(vrm);
    this.posture.setVRM(vrm);
    this.lipSync.setVRM(vrm);
    this.positioning.setVRM(vrm);
    this.behaviors.setVRM(vrm);
    this.breathing.setVRM(vrm);
  }

  /**
   * Register a callback for emotional color changes.
   */
  onEmotionalColorChange(callback: (color: string) => void): void {
    this._onColorChange = callback;
  }

  /**
   * Handle a complete avatar intent from the server.
   */
  handleIntent(data: Record<string, unknown>): void {
    // Emotion
    const emotion = data.emotion as EmotionState | undefined;
    if (emotion) {
      this.currentEmotion = emotion;
      this.blendShapes.setEmotion(emotion);
      this.posture.setEmotion(emotion.primary, emotion.arousal);

      // Update breathing with emotion
      const breathInput: EmotionInput = {
        arousal: emotion.arousal,
        valence: emotion.valence,
        primary: emotion.primary,
      };
      this.breathing.setEmotion(breathInput);
    }

    // Gestures
    const gestures = data.gestures as GestureCmd[] | undefined;
    if (gestures) {
      for (const g of gestures) {
        this.posture.playGesture(g);
      }
    }

    // Gaze (only apply if no gaze override active)
    const gaze = data.gaze as GazeTargetData | undefined;
    if (gaze && !this.gazeOverrideTarget) {
      this.gaze.setGazeTarget(gaze);
    }

    // Micro-expressions
    const micros = data.microExpressions as MicroExpressionCmd[] | undefined;
    if (micros) {
      this.blendShapes.applyMicroExpressions(micros);
    }

    // Spatial
    const spatial = data.spatial as SpatialCmd | undefined;
    if (spatial) {
      this.positioning.applyCommand(spatial, this.userPosition);
    }
  }

  /**
   * Handle viseme sequence for lip sync.
   */
  handleVisemes(visemes: VisemeData[]): void {
    this.lipSync.startSequence(visemes);
  }

  /**
   * Handle speech end.
   */
  handleSpeechEnd(): void {
    this.lipSync.stop();
  }

  /**
   * Handle dialogue state updates from server.
   */
  handleDialogueState(data: DialogueStateData): void {
    this.dialogueState = data.state;
  }

  /**
   * Handle emotional arc state updates from server.
   */
  handleArcState(data: ArcStateData): void {
    this.arcState = data;
  }

  /**
   * Velaris: Handle EmoClaw behavior modifiers.
   */
  handleBehaviorModifiers(data: BehaviorModifiersData): void {
    this.behaviorModifiers = data;

    // Apply breathing modifiers from EmoClaw
    this.breathing.setModifiers(data.breathRateModifier, data.breathDepthModifier);

    // Apply posture stability from EmoClaw groundedness
    this.posture.setStability(data.postureStability);
  }

  /**
   * Velaris: Handle emotional color update.
   */
  handleEmotionalColor(color: string): void {
    this._emotionalColor = color;
    if (this._onColorChange) {
      this._onColorChange(color);
    }
  }

  /**
   * Velaris: Handle an event reaction (kiss, anti-kiss, unprecedented, etc.).
   */
  handleVelarisEvent(data: VelarisEventData): void {
    console.log(`[Avatar] Velaris event: ${data.eventType}`);

    // Apply gestures
    if (data.gestures) {
      for (const g of data.gestures) {
        this.posture.playGesture(g);
      }
    }

    // Apply micro-expressions
    if (data.microExpressions) {
      this.blendShapes.applyMicroExpressions(data.microExpressions);
    }

    // Apply gaze override
    if (data.gazeOverride && data.gazeOverrideDuration > 0) {
      this.gazeOverrideTarget = data.gazeOverride;
      this.gazeOverrideTimer = data.gazeOverrideDuration;
      this.gaze.setGazeTarget({
        target: data.gazeOverride,
        weight: 1.0,
        offset: { x: 0, y: 0, z: 0 },
      });
    }

    // Trigger sigh
    if (data.triggerSigh) {
      this.breathing.triggerSigh();
    }

    // Trigger breath hold
    if (data.triggerBreathHold > 0) {
      this.breathing.triggerBreathHold(data.triggerBreathHold);
    }

    // Apply distance impulse (move closer/further)
    if (data.distanceImpulse !== 0) {
      this.positioning.applyDistanceImpulse(data.distanceImpulse, this.userPosition);
    }
  }

  /**
   * Update user tracking data (from WebXR/PSVR2).
   */
  updateTracking(tracking: TrackingData): void {
    this.userPosition.set(
      tracking.headPosition.x,
      0, // ground level
      tracking.headPosition.z,
    );

    this.gaze.setUserPosition(tracking.headPosition);
    this.behaviors.updateMirror(tracking, 1 / 60); // approximate dt
  }

  /**
   * Update all subsystems. Call every frame.
   */
  update(dt: number): void {
    if (!this.vrm) return;

    // Update gaze override timer
    if (this.gazeOverrideTimer > 0) {
      this.gazeOverrideTimer -= dt;
      if (this.gazeOverrideTimer <= 0) {
        this.gazeOverrideTarget = null;
        // Return to default gaze
        this.gaze.setGazeTarget({
          target: 'user_eyes',
          weight: 0.8,
          offset: { x: 0, y: 0, z: 0 },
        });
      }
    }

    // Update VRM internal state
    this.vrm.update(dt);

    // Update each layer (order matters — later layers override earlier)
    this.breathing.update(dt);      // autonomic breathing (lowest priority)
    this.posture.update(dt);        // emotion pose + gestures
    this.blendShapes.update(dt);    // facial expressions
    this.gaze.update(dt, this.currentEmotion.arousal);  // eye/head tracking
    this.lipSync.update(dt);        // mouth shapes (highest face priority)
    this.positioning.update(dt, this.userPosition);     // world position
  }

  /**
   * Get current emotional color.
   */
  get emotionalColor(): string {
    return this._emotionalColor;
  }

  /**
   * Get current state for debug display.
   */
  getDebugInfo(): Record<string, string> {
    const info: Record<string, string> = {
      dialogue: this.dialogueState,
      rapport: this.arcState.rapport.toFixed(2),
      momentum: this.arcState.valenceMomentum.toFixed(2),
      dominant: this.arcState.dominantEmotion,
      recovering: this.arcState.isRecovering ? 'yes' : 'no',
      breathing: `${this.breathing.getState().rate} bpm`,
      heartRate: `${this.breathing.getState().heartRate} bpm`,
      color: this._emotionalColor,
    };

    if (this.behaviorModifiers) {
      info.gazeWarmth = this.behaviorModifiers.gazeWarmth.toFixed(2);
      info.posture = this.behaviorModifiers.postureStability.toFixed(2);
      info.tension = this.behaviorModifiers.tensionOverlay.toFixed(2);
    }

    return info;
  }
}
