/**
 * Transition curves — easing functions and interpolation utilities.
 */

/** Ease-in-out cubic — smooth start and end. */
export function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

/** Ease-out cubic — fast start, slow end. Good for settling. */
export function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

/** Ease-in cubic — slow start, fast end. Good for anticipation. */
export function easeInCubic(t: number): number {
  return t * t * t;
}

/** Ease-out elastic — slight overshoot then settle. Natural motion. */
export function easeOutElastic(t: number): number {
  if (t === 0 || t === 1) return t;
  return Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (2 * Math.PI / 3)) + 1;
}

/** Smooth overshoot and settle — like a spring. */
export function easeOutBack(t: number): number {
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
}

/** Clamp value between min and max. */
export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

/** Linear interpolation. */
export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * clamp(t, 0, 1);
}

/** Damped lerp — framerate-independent smoothing.
 *  smoothing: 0 = instant, higher = slower (try 5-15)
 */
export function damp(current: number, target: number, smoothing: number, dt: number): number {
  return lerp(current, target, 1 - Math.exp(-smoothing * dt));
}

/**
 * Animated value with automatic smooth transitions.
 */
export class SmoothValue {
  current: number;
  target: number;
  velocity: number = 0;
  smoothing: number;

  constructor(initial: number = 0, smoothing: number = 8) {
    this.current = initial;
    this.target = initial;
    this.smoothing = smoothing;
  }

  set(value: number): void {
    this.target = value;
  }

  update(dt: number): number {
    this.current = damp(this.current, this.target, this.smoothing, dt);
    return this.current;
  }

  get settled(): boolean {
    return Math.abs(this.current - this.target) < 0.001;
  }
}
