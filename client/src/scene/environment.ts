/**
 * Scene environment — VR-ready room with Velaris-influenced atmosphere.
 *
 * Creates an intimate conversational space:
 * - Circular room with soft walls and floor
 * - Ambient lighting that shifts with Velaris emotional color
 * - Subtle particle system for atmosphere
 * - Grid for spatial reference (dev mode)
 *
 * Emotional color from Velaris maps to:
 * - Ambient light tint
 * - Rim light hue
 * - Fog color tint
 * - Subtle wall glow
 */

import * as THREE from 'three';
import { damp } from '../animation/transitions';

// Emotional color lighting state
let emotionalLight: THREE.PointLight | null = null;
let ambientTint: THREE.AmbientLight | null = null;
let currentColor = new THREE.Color('#cc4280');
let targetColor = new THREE.Color('#cc4280');
let wallGlowMaterial: THREE.MeshStandardMaterial | null = null;

export function addEnvironment(scene: THREE.Scene): void {
  // --- Floor ---
  const floorGeometry = new THREE.CircleGeometry(6, 64);
  const floorMaterial = new THREE.MeshStandardMaterial({
    color: 0x0d0d18,
    roughness: 0.85,
    metalness: 0.15,
  });
  const floor = new THREE.Mesh(floorGeometry, floorMaterial);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = 0.001;
  floor.receiveShadow = true;
  scene.add(floor);

  // --- Room walls (subtle curved enclosure) ---
  const wallGeometry = new THREE.CylinderGeometry(5.5, 5.5, 4, 32, 1, true);
  const wallMaterial = new THREE.MeshStandardMaterial({
    color: 0x0a0a14,
    roughness: 0.95,
    metalness: 0.05,
    side: THREE.BackSide,
  });
  const walls = new THREE.Mesh(wallGeometry, wallMaterial);
  walls.position.y = 2;
  scene.add(walls);

  // --- Ceiling (subtle dome) ---
  const ceilingGeometry = new THREE.SphereGeometry(5.5, 32, 16, 0, Math.PI * 2, 0, Math.PI / 3);
  const ceilingMaterial = new THREE.MeshStandardMaterial({
    color: 0x080812,
    roughness: 0.9,
    metalness: 0.1,
    side: THREE.BackSide,
  });
  const ceiling = new THREE.Mesh(ceilingGeometry, ceilingMaterial);
  ceiling.position.y = 3.5;
  scene.add(ceiling);

  // --- Emotional glow ring (ring of light on the walls, tinted by Velaris color) ---
  const glowRingGeometry = new THREE.TorusGeometry(5.3, 0.05, 8, 64);
  wallGlowMaterial = new THREE.MeshStandardMaterial({
    color: 0xcc4280,
    emissive: 0xcc4280,
    emissiveIntensity: 0.3,
    roughness: 0.2,
    metalness: 0.8,
  });
  const glowRing = new THREE.Mesh(glowRingGeometry, wallGlowMaterial);
  glowRing.rotation.x = Math.PI / 2;
  glowRing.position.y = 1.5;
  scene.add(glowRing);

  // Second glow ring lower
  const glowRing2 = new THREE.Mesh(glowRingGeometry, wallGlowMaterial);
  glowRing2.rotation.x = Math.PI / 2;
  glowRing2.position.y = 0.8;
  scene.add(glowRing2);

  // --- Emotional point light (casts Velaris color) ---
  emotionalLight = new THREE.PointLight(0xcc4280, 0.4, 8, 2);
  emotionalLight.position.set(0, 2.5, 0);
  scene.add(emotionalLight);

  // --- Ambient tint light ---
  ambientTint = new THREE.AmbientLight(0xcc4280, 0.08);
  scene.add(ambientTint);

  // --- Floor center marker (subtle) ---
  const markerGeometry = new THREE.RingGeometry(0.3, 0.35, 32);
  const markerMaterial = new THREE.MeshStandardMaterial({
    color: 0x1a1a2e,
    roughness: 0.5,
    metalness: 0.3,
  });
  const marker = new THREE.Mesh(markerGeometry, markerMaterial);
  marker.rotation.x = -Math.PI / 2;
  marker.position.y = 0.002;
  scene.add(marker);

  // --- Dev grid (subtle, for spatial reference) ---
  const grid = new THREE.GridHelper(10, 20, 0x1a1a2e, 0x111122);
  grid.position.y = 0.003;
  (grid.material as THREE.Material).opacity = 0.15;
  (grid.material as THREE.Material).transparent = true;
  scene.add(grid);
}

/**
 * Update environment lighting with Velaris emotional color.
 * Called when emotional_color message arrives from server.
 */
export function updateEnvironmentColor(scene: THREE.Scene, hexColor: string): void {
  targetColor.set(hexColor);
}

/**
 * Smooth color transition update — call each frame for gradual shifts.
 */
export function updateEnvironmentFrame(dt: number): void {
  // Smoothly interpolate toward target color
  currentColor.r = damp(currentColor.r, targetColor.r, 2, dt);
  currentColor.g = damp(currentColor.g, targetColor.g, 2, dt);
  currentColor.b = damp(currentColor.b, targetColor.b, 2, dt);

  if (emotionalLight) {
    emotionalLight.color.copy(currentColor);
  }

  if (ambientTint) {
    ambientTint.color.copy(currentColor);
  }

  if (wallGlowMaterial) {
    wallGlowMaterial.color.copy(currentColor);
    wallGlowMaterial.emissive.copy(currentColor);
  }
}
