/**
 * VRM model loader — loads .vrm avatar files using @pixiv/three-vrm.
 *
 * Supports:
 * - Loading from URL or file path
 * - Downloading a default VRM if none specified
 * - Accessing VRM blend shapes and bone structure
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, VRM } from '@pixiv/three-vrm';

export class AvatarLoader {
  private loader: GLTFLoader;

  constructor() {
    this.loader = new GLTFLoader();
    this.loader.register((parser) => new VRMLoaderPlugin(parser));
  }

  /**
   * Load a VRM model from a URL.
   */
  async load(url: string): Promise<VRM> {
    return new Promise((resolve, reject) => {
      this.loader.load(
        url,
        (gltf) => {
          const vrm = gltf.userData.vrm as VRM | undefined;
          if (!vrm) {
            reject(new Error('No VRM data found in loaded model'));
            return;
          }

          // Rotate model to face camera (VRM models face +Z by default)
          vrm.scene.rotation.y = Math.PI;

          // Enable shadow casting
          vrm.scene.traverse((obj) => {
            if (obj instanceof THREE.Mesh) {
              obj.castShadow = true;
              obj.receiveShadow = true;
            }
          });

          console.log('[Avatar] VRM loaded successfully');
          console.log('[Avatar] Available expressions:', this.listExpressions(vrm));

          resolve(vrm);
        },
        (progress) => {
          if (progress.total > 0) {
            const pct = Math.round((progress.loaded / progress.total) * 100);
            console.log(`[Avatar] Loading: ${pct}%`);
          }
        },
        (error) => {
          reject(error);
        },
      );
    });
  }

  /**
   * List available expression (blend shape) names on a VRM model.
   */
  listExpressions(vrm: VRM): string[] {
    const names: string[] = [];
    if (vrm.expressionManager) {
      const expressionMap = vrm.expressionManager.expressionMap;
      for (const name in expressionMap) {
        names.push(name);
      }
    }
    return names;
  }

  /**
   * Create a placeholder avatar (a simple humanoid shape) for testing
   * when no VRM model is available.
   */
  createPlaceholder(): THREE.Group {
    const group = new THREE.Group();
    const material = new THREE.MeshStandardMaterial({
      color: 0x6666aa,
      roughness: 0.7,
      metalness: 0.2,
    });

    // Head
    const head = new THREE.Mesh(
      new THREE.SphereGeometry(0.12, 16, 16),
      material,
    );
    head.position.set(0, 1.6, 0);
    head.castShadow = true;
    group.add(head);

    // Body (capsule approximation)
    const body = new THREE.Mesh(
      new THREE.CylinderGeometry(0.15, 0.12, 0.6, 12),
      material,
    );
    body.position.set(0, 1.15, 0);
    body.castShadow = true;
    group.add(body);

    // Legs
    const legMaterial = material.clone();
    for (const side of [-0.08, 0.08]) {
      const leg = new THREE.Mesh(
        new THREE.CylinderGeometry(0.05, 0.04, 0.8, 8),
        legMaterial,
      );
      leg.position.set(side, 0.45, 0);
      leg.castShadow = true;
      group.add(leg);
    }

    // Eyes
    const eyeMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      emissive: 0x4488ff,
      emissiveIntensity: 0.5,
    });
    for (const side of [-0.04, 0.04]) {
      const eye = new THREE.Mesh(
        new THREE.SphereGeometry(0.02, 8, 8),
        eyeMaterial,
      );
      eye.position.set(side, 1.63, 0.1);
      group.add(eye);
    }

    return group;
  }
}
