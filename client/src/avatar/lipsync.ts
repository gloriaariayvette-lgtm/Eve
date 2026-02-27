/**
 * Lip sync driver — applies viseme shapes to VRM mouth blend shapes.
 *
 * Receives timed viseme sequences from the server and interpolates
 * between them to produce smooth mouth movements during speech.
 *
 * VRM Expression mapping:
 *   aa → open mouth (a sound)
 *   ee → spread lips (e/i sound)
 *   ih → short i
 *   oh → round lips (o sound)
 *   ou → tight round (u/oo sound)
 */

import { VRM } from '@pixiv/three-vrm';
import { damp } from '../animation/transitions';

export interface VisemeData {
  shape: string;   // "AA", "EE", "IH", "OH", "OO", "PP", "FF", "TH", "DD", "KK", "CH", "SS", "NN", "RR", "SILENT"
  weight: number;
  timestamp: number;
}

// Map server viseme shapes to VRM expression names and weights
const VISEME_TO_VRM: Record<string, { expression: string; weight: number }[]> = {
  SILENT: [],
  PP:     [{ expression: 'ou', weight: 0.5 }],    // lips pressed
  FF:     [{ expression: 'ih', weight: 0.3 }],    // lower lip in
  TH:     [{ expression: 'ih', weight: 0.2 }],    // tongue between teeth
  DD:     [{ expression: 'ih', weight: 0.3 }],    // tongue on ridge
  KK:     [{ expression: 'oh', weight: 0.2 }],    // back of tongue
  CH:     [{ expression: 'ih', weight: 0.4 }],    // tongue behind teeth
  SS:     [{ expression: 'ee', weight: 0.2 }],    // teeth together
  NN:     [{ expression: 'ih', weight: 0.2 }],    // nasal
  RR:     [{ expression: 'oh', weight: 0.2 }],    // tongue curled
  AA:     [{ expression: 'aa', weight: 0.8 }],    // open mouth
  EE:     [{ expression: 'ee', weight: 0.7 }],    // spread lips
  IH:     [{ expression: 'ih', weight: 0.5 }],    // short i
  OH:     [{ expression: 'oh', weight: 0.7 }],    // round lips
  OO:     [{ expression: 'ou', weight: 0.8 }],    // tight round
};

// All mouth-related expressions we control
const MOUTH_EXPRESSIONS = ['aa', 'ee', 'ih', 'oh', 'ou'];

export class LipSyncDriver {
  private vrm: VRM | null = null;
  private visemes: VisemeData[] = [];
  private startTime = 0;
  private isSpeaking = false;

  // Current mouth shape targets (smooth values)
  private mouthTargets: Record<string, number> = {};
  private mouthCurrent: Record<string, number> = {};

  constructor() {
    for (const expr of MOUTH_EXPRESSIONS) {
      this.mouthTargets[expr] = 0;
      this.mouthCurrent[expr] = 0;
    }
  }

  setVRM(vrm: VRM): void {
    this.vrm = vrm;
  }

  /**
   * Start a viseme sequence for lip sync.
   */
  startSequence(visemes: VisemeData[]): void {
    this.visemes = visemes;
    this.startTime = performance.now() / 1000;
    this.isSpeaking = true;
  }

  /**
   * Stop lip sync.
   */
  stop(): void {
    this.isSpeaking = false;
    // Fade all mouth shapes to 0
    for (const expr of MOUTH_EXPRESSIONS) {
      this.mouthTargets[expr] = 0;
    }
  }

  /**
   * Update lip sync. Call every frame.
   */
  update(dt: number): void {
    if (!this.vrm?.expressionManager) return;

    if (this.isSpeaking && this.visemes.length > 0) {
      const elapsed = performance.now() / 1000 - this.startTime;
      this._updateVisemeTargets(elapsed);
    }

    // Smooth all mouth shapes
    for (const expr of MOUTH_EXPRESSIONS) {
      this.mouthCurrent[expr] = damp(
        this.mouthCurrent[expr],
        this.mouthTargets[expr],
        15,  // fast smoothing for responsive lip sync
        dt,
      );

      if (this.mouthCurrent[expr] > 0.01) {
        this.vrm.expressionManager.setValue(expr, this.mouthCurrent[expr]);
      } else {
        this.vrm.expressionManager.setValue(expr, 0);
      }
    }
  }

  get speaking(): boolean {
    return this.isSpeaking;
  }

  private _updateVisemeTargets(elapsed: number): void {
    // Find current viseme based on timestamp
    let currentViseme: VisemeData | null = null;
    let nextViseme: VisemeData | null = null;

    for (let i = 0; i < this.visemes.length; i++) {
      if (this.visemes[i].timestamp <= elapsed) {
        currentViseme = this.visemes[i];
        nextViseme = this.visemes[i + 1] ?? null;
      } else {
        break;
      }
    }

    // Past end of sequence
    if (!currentViseme || (elapsed > (this.visemes[this.visemes.length - 1]?.timestamp ?? 0) + 0.3)) {
      this.stop();
      return;
    }

    // Reset all targets
    for (const expr of MOUTH_EXPRESSIONS) {
      this.mouthTargets[expr] = 0;
    }

    // Apply current viseme
    const mappings = VISEME_TO_VRM[currentViseme.shape] ?? [];
    for (const m of mappings) {
      this.mouthTargets[m.expression] = m.weight * currentViseme.weight;
    }

    // Interpolate toward next viseme if available
    if (nextViseme) {
      const segDuration = nextViseme.timestamp - currentViseme.timestamp;
      if (segDuration > 0) {
        const t = (elapsed - currentViseme.timestamp) / segDuration;
        const nextMappings = VISEME_TO_VRM[nextViseme.shape] ?? [];

        for (const m of nextMappings) {
          const current = this.mouthTargets[m.expression] ?? 0;
          this.mouthTargets[m.expression] = current + (m.weight * nextViseme.weight - current) * t;
        }
      }
    }
  }
}
