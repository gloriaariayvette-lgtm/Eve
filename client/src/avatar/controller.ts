/**
 * Master avatar controller — orchestrates all avatar subsystems.
 *
 * Receives commands from the WebSocket connection and routes them
 * to the appropriate subsystem (blendshapes, gaze, posture, lipsync, spatial).
 * Updates all systems each frame.
 */

import * as THREE from 'three';
import { VRM } from '@pixiv/three-vrm';
import { BlendShapeDriver, EmotionState, MicroExpressionCmd } from './blendshapes';
import { GazeController, GazeTargetData } from './gaze';
import { PostureController, GestureCmd } from './posture';
import { LipSyncDriver, VisemeData } from './lipsync';
import { AvatarPositioning, SpatialCmd } from '../spatial/positioning';
import { SpatialBehaviors, TrackingData } from '../spatial/behaviors';

export class AvatarController {
  readonly blendShapes = new BlendShapeDriver();
  readonly gaze = new GazeController();
  readonly posture = new PostureController();
  readonly lipSync = new LipSyncDriver();
  readonly positioning = new AvatarPositioning();
  readonly behaviors = new SpatialBehaviors();

  private vrm: VRM | null = null;
  private currentEmotion: EmotionState = {
    primary: 'neutral',
    valence: 0,
    arousal: 0.2,
    dominance: 0.5,
  };

  // User position for spatial calculations
  private userPosition = new THREE.Vector3(0, 0, 2.0);

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
    this.posture.update(dt);
    this.blendShapes.update(dt);
    this.gaze.update(dt, this.currentEmotion.arousal);
    this.lipSync.update(dt);
    this.positioning.update(dt, this.userPosition);
  }
}
