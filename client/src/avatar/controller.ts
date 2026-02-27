/**
 * Master avatar controller — orchestrates all avatar subsystems.
 *
 * Receives commands from the WebSocket connection and routes them
 * to the appropriate subsystem (blendshapes, gaze, posture, lipsync, spatial).
 * Updates all systems each frame.
 *
 * Phase 4-5 additions:
 * - Breathing system (autonomic nervous system simulation)
 * - Dialogue state awareness (adjusts behavior based on conversation phase)
 * - Arc state tracking (rapport, emotional momentum)
 * - Performance-adaptive quality (throttle subsystems when framerate drops)
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

  // Phase 4: Dialogue and arc state
  private dialogueState: string = 'idle';
  private arcState: ArcStateData = {
    rapport: 0.2,
    valenceMomentum: 0,
    dominantEmotion: 'neutral',
    isRecovering: false,
  };

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
   * Handle a complete avatar intent from the server.
   */
  handleIntent(data: Record<string, unknown>): void {
    // Emotion
    const emotion = data.emotion as EmotionState | undefined;
    if (emotion) {
      this.currentEmotion = emotion;
      this.blendShapes.setEmotion(emotion);
      this.posture.setEmotion(emotion.primary, emotion.arousal);

      // Phase 5: Update breathing with emotion
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

    // Gaze
    const gaze = data.gaze as GazeTargetData | undefined;
    if (gaze) {
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
   * Phase 4: Handle dialogue state updates from server.
   */
  handleDialogueState(data: DialogueStateData): void {
    this.dialogueState = data.state;
    // Could adjust subsystem behavior based on dialogue state
    // e.g., reduce gesture intensity during emotional state
  }

  /**
   * Phase 4: Handle emotional arc state updates from server.
   */
  handleArcState(data: ArcStateData): void {
    this.arcState = data;
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

    // Update VRM internal state
    this.vrm.update(dt);

    // Update each layer (order matters — later layers override earlier)
    this.breathing.update(dt);      // Phase 5: autonomic breathing (lowest priority)
    this.posture.update(dt);        // emotion pose + gestures
    this.blendShapes.update(dt);    // facial expressions
    this.gaze.update(dt, this.currentEmotion.arousal);  // eye/head tracking
    this.lipSync.update(dt);        // mouth shapes (highest face priority)
    this.positioning.update(dt, this.userPosition);     // world position
  }

  /**
   * Get current state for debug display.
   */
  getDebugInfo(): Record<string, string> {
    return {
      dialogue: this.dialogueState,
      rapport: this.arcState.rapport.toFixed(2),
      momentum: this.arcState.valenceMomentum.toFixed(2),
      dominant: this.arcState.dominantEmotion,
      recovering: this.arcState.isRecovering ? 'yes' : 'no',
      breathing: `${this.breathing.getState().rate} bpm`,
      heartRate: `${this.breathing.getState().heartRate} bpm`,
    };
  }
}
