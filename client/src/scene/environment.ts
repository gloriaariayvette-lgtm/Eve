/**
 * Scene environment — optional room geometry and atmosphere.
 */

import * as THREE from 'three';

export function addEnvironment(scene: THREE.Scene): void {
  // Subtle gradient background (dark to slightly lighter at horizon)
  // Already handled by fog in setup.ts

  // Optional: grid helper for spatial reference during development
  const grid = new THREE.GridHelper(10, 20, 0x1a1a2e, 0x111122);
  grid.position.y = 0.001; // slightly above ground to avoid z-fighting
  (grid.material as THREE.Material).opacity = 0.3;
  (grid.material as THREE.Material).transparent = true;
  scene.add(grid);
}
