/**
 * Main animation loop — 60-90fps requestAnimationFrame with delta time.
 */

export type UpdateCallback = (dt: number, elapsed: number) => void;

export class AnimationLoop {
  private callbacks: UpdateCallback[] = [];
  private running = false;
  private lastTime = 0;
  private elapsed = 0;
  private frameCount = 0;
  private fpsUpdateTime = 0;
  private currentFps = 0;
  private animationFrameId = 0;

  /**
   * Register an update callback. Called every frame with (deltaTime, elapsedTime).
   */
  onUpdate(callback: UpdateCallback): void {
    this.callbacks.push(callback);
  }

  /**
   * Start the animation loop.
   */
  start(): void {
    if (this.running) return;
    this.running = true;
    this.lastTime = performance.now() / 1000;
    this.fpsUpdateTime = this.lastTime;
    this.tick();
  }

  /**
   * Stop the animation loop.
   */
  stop(): void {
    this.running = false;
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
  }

  get fps(): number {
    return this.currentFps;
  }

  private tick = (): void => {
    if (!this.running) return;

    const now = performance.now() / 1000;
    const dt = Math.min(now - this.lastTime, 0.05); // cap at 50ms (20fps min)
    this.lastTime = now;
    this.elapsed += dt;
    this.frameCount++;

    // FPS counter (update every 0.5s)
    if (now - this.fpsUpdateTime >= 0.5) {
      this.currentFps = Math.round(this.frameCount / (now - this.fpsUpdateTime));
      this.frameCount = 0;
      this.fpsUpdateTime = now;
    }

    // Call all update handlers
    for (const cb of this.callbacks) {
      cb(dt, this.elapsed);
    }

    this.animationFrameId = requestAnimationFrame(this.tick);
  };
}
