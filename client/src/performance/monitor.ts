/**
 * Performance monitor — tracks frame budget, detects drops, adapts quality.
 *
 * Monitors:
 * - Frame time (ms per frame) with rolling average
 * - Frame drops (missed 16.67ms budget at 60fps)
 * - Memory pressure (if available via performance API)
 * - GPU load estimation (via frame time variance)
 *
 * Emits quality level recommendations: "high", "medium", "low"
 * that other systems can use to reduce work when performance degrades.
 */

export type QualityLevel = 'high' | 'medium' | 'low';

export interface PerformanceSnapshot {
  fps: number;
  avgFrameTime: number;   // ms
  maxFrameTime: number;   // ms over last window
  dropRate: number;        // fraction of frames that exceeded budget
  qualityLevel: QualityLevel;
  memoryMB: number;        // approximate JS heap, 0 if unavailable
}

export type QualityChangeCallback = (level: QualityLevel, snapshot: PerformanceSnapshot) => void;

const TARGET_FPS = 60;
const FRAME_BUDGET_MS = 1000 / TARGET_FPS; // ~16.67ms
const HISTORY_SIZE = 120; // 2 seconds at 60fps

export class PerformanceMonitor {
  private frameTimes: number[] = [];
  private currentLevel: QualityLevel = 'high';
  private callbacks: QualityChangeCallback[] = [];
  private lastEvalTime = 0;
  private evalInterval = 2.0; // evaluate every 2 seconds
  private consecutiveLowFrames = 0;
  private consecutiveHighFrames = 0;

  // Thresholds
  private readonly dropThresholdMedium = 0.1;  // 10% drops → medium
  private readonly dropThresholdLow = 0.25;     // 25% drops → low
  private readonly recoveryFrames = 180;        // 3 seconds of good frames to recover

  /**
   * Register a callback for quality level changes.
   */
  onQualityChange(callback: QualityChangeCallback): void {
    this.callbacks.push(callback);
  }

  /**
   * Record a frame. Call once per animation frame.
   * @param frameTimeMs Time taken for the frame in milliseconds.
   */
  recordFrame(frameTimeMs: number): void {
    this.frameTimes.push(frameTimeMs);
    if (this.frameTimes.length > HISTORY_SIZE) {
      this.frameTimes.shift();
    }

    // Track consecutive good/bad frames
    if (frameTimeMs > FRAME_BUDGET_MS * 1.5) {
      this.consecutiveLowFrames++;
      this.consecutiveHighFrames = 0;
    } else {
      this.consecutiveHighFrames++;
      this.consecutiveLowFrames = 0;
    }
  }

  /**
   * Evaluate performance and potentially adjust quality.
   * Call periodically (e.g., every frame, internally throttled).
   */
  evaluate(elapsed: number): void {
    if (elapsed - this.lastEvalTime < this.evalInterval) return;
    this.lastEvalTime = elapsed;

    if (this.frameTimes.length < 30) return; // need enough data

    const snapshot = this.getSnapshot();
    const newLevel = this._computeLevel(snapshot);

    if (newLevel !== this.currentLevel) {
      this.currentLevel = newLevel;
      for (const cb of this.callbacks) {
        cb(newLevel, snapshot);
      }
    }
  }

  /**
   * Get current performance snapshot.
   */
  getSnapshot(): PerformanceSnapshot {
    const times = this.frameTimes;
    const avg = times.reduce((a, b) => a + b, 0) / times.length;
    const max = Math.max(...times);
    const drops = times.filter(t => t > FRAME_BUDGET_MS * 1.5).length;
    const dropRate = drops / times.length;

    let memoryMB = 0;
    const perf = performance as Performance & { memory?: { usedJSHeapSize: number } };
    if (perf.memory) {
      memoryMB = Math.round(perf.memory.usedJSHeapSize / (1024 * 1024));
    }

    return {
      fps: avg > 0 ? Math.round(1000 / avg) : 0,
      avgFrameTime: Math.round(avg * 100) / 100,
      maxFrameTime: Math.round(max * 100) / 100,
      dropRate: Math.round(dropRate * 1000) / 1000,
      qualityLevel: this.currentLevel,
      memoryMB,
    };
  }

  get quality(): QualityLevel {
    return this.currentLevel;
  }

  private _computeLevel(snapshot: PerformanceSnapshot): QualityLevel {
    const { dropRate } = snapshot;

    // Degrade quickly
    if (dropRate >= this.dropThresholdLow || this.consecutiveLowFrames > 30) {
      return 'low';
    }
    if (dropRate >= this.dropThresholdMedium || this.consecutiveLowFrames > 15) {
      return 'medium';
    }

    // Recover slowly (hysteresis to prevent flapping)
    if (this.currentLevel === 'low') {
      return this.consecutiveHighFrames > this.recoveryFrames ? 'medium' : 'low';
    }
    if (this.currentLevel === 'medium') {
      return this.consecutiveHighFrames > this.recoveryFrames ? 'high' : 'medium';
    }

    return 'high';
  }
}

/**
 * Quality-aware settings that subsystems can query.
 */
export class AdaptiveQuality {
  private level: QualityLevel = 'high';

  constructor(monitor: PerformanceMonitor) {
    monitor.onQualityChange((level) => {
      this.level = level;
      console.log(`[Quality] Level changed to: ${level}`);
    });
  }

  /** Shadow map resolution. */
  get shadowMapSize(): number {
    return this.level === 'high' ? 2048 : this.level === 'medium' ? 1024 : 512;
  }

  /** Whether to enable micro-saccades. */
  get enableSaccades(): boolean {
    return this.level !== 'low';
  }

  /** Whether to enable micro-expressions. */
  get enableMicroExpressions(): boolean {
    return this.level !== 'low';
  }

  /** Maximum active gestures at once. */
  get maxActiveGestures(): number {
    return this.level === 'high' ? 4 : this.level === 'medium' ? 2 : 1;
  }

  /** Blend shape update frequency (1 = every frame, 2 = every other). */
  get blendShapeUpdateInterval(): number {
    return this.level === 'high' ? 1 : this.level === 'medium' ? 1 : 2;
  }

  /** Whether to run idle subtle animations. */
  get enableIdleSubtleties(): boolean {
    return this.level !== 'low';
  }

  /** Pixel ratio cap. */
  get maxPixelRatio(): number {
    return this.level === 'high' ? 2 : this.level === 'medium' ? 1.5 : 1;
  }
}
