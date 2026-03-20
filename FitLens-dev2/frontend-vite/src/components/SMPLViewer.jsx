import { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

const VIEWER_HEIGHT = 500;

// Build a BufferGeometry directly from the backend x/y/z/i/j/k arrays.
// Vertices arrive in centimetres — convert to metres for Three.js.
// SMPL coordinate system: Y-up, person faces +Z in rest pose.
// We rotate 180° around Y so the person faces the camera (which looks down -Z).
const buildGeometry = (meshData) => {
  const { x, y, z, i, j, k } = meshData;
  const n = x.length;

  const positions = new Float32Array(n * 3);
  for (let v = 0; v < n; v++) {
    // Flip Z so person faces camera: SMPL +Z → Three.js -Z (front-facing)
    positions[v * 3]     =  x[v] / 100;   // X: left/right (unchanged)
    positions[v * 3 + 1] =  y[v] / 100;   // Y: up (unchanged, feet=0)
    positions[v * 3 + 2] = -z[v] / 100;   // Z: flip so person faces camera
  }

  const indices = new Uint32Array(i.length * 3);
  for (let f = 0; f < i.length; f++) {
    indices[f * 3]     = i[f];
    indices[f * 3 + 1] = j[f];
    indices[f * 3 + 2] = k[f];
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geo.setIndex(new THREE.BufferAttribute(indices, 1));
  geo.computeVertexNormals();
  return geo;
};

// Translate the mesh so feet sit at Y=0 and X/Z are centred on the origin.
// Returns the bounding box AFTER centering (world space).
const centreAtOrigin = (mesh) => {
  // Compute bounding box in local space before any position offset
  mesh.geometry.computeBoundingBox();
  const box = mesh.geometry.boundingBox.clone();

  const cx = (box.min.x + box.max.x) / 2;
  const cz = (box.min.z + box.max.z) / 2;

  // Shift geometry so feet are at Y=0 and body is centred on X/Z origin
  mesh.geometry.translate(-cx, -box.min.y, -cz);
  mesh.geometry.computeBoundingBox();

  // Keep mesh.position at origin — all centering is baked into geometry
  mesh.position.set(0, 0, 0);
};

// Position camera so the full body fills the viewport, looking at mid-torso.
const frameCamera = (camera, controls, mesh, lights) => {
  mesh.geometry.computeBoundingBox();
  const box  = mesh.geometry.boundingBox;
  const size = new THREE.Vector3();
  box.getSize(size);

  const maxDim   = Math.max(size.x, size.y, size.z, 0.1);
  const fov      = THREE.MathUtils.degToRad(camera.fov);
  const distance = (maxDim / (2 * Math.tan(fov / 2))) * 1.6;

  // Look at mid-torso (55% up from feet)
  const targetY = size.y * 0.55;
  const target  = new THREE.Vector3(0, targetY, 0);

  camera.near = Math.max(0.001, distance / 200);
  camera.far  = distance * 25;
  // Camera sits in front of the person (+Z side, since we flipped Z in buildGeometry)
  camera.position.set(0, targetY, distance);
  camera.lookAt(target);
  camera.updateProjectionMatrix();

  controls.target.copy(target);
  controls.update();

  if (lights) {
    lights.key.position.set( distance,        distance * 1.2,  distance * 0.8);
    lights.fill.position.set(-distance * 0.8, distance * 0.5,  distance * 0.6);
    lights.back.position.set(0,               distance * 0.7, -distance);
  }
};

const disposeMesh = (obj) => {
  obj?.traverse((child) => {
    child.geometry?.dispose();
    if (Array.isArray(child.material)) child.material.forEach((m) => m?.dispose?.());
    else child.material?.dispose?.();
  });
};

// ─────────────────────────────────────────────────────────────────────────────

const SMPLViewer = ({ meshData, statusText, statusDetail }) => {
  const containerRef = useRef(null);
  const rendererRef  = useRef(null);
  const meshRef      = useRef(null);
  const [isReady,    setIsReady]    = useState(false);
  const [loadError,  setLoadError]  = useState(null);

  useEffect(() => {
    if (!containerRef.current || !meshData?.x?.length) return;

    setIsReady(false);
    setLoadError(null);
    let disposed = false;

    // ── Scene ──────────────────────────────────────────────────────────────
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#1a1a2e');

    // ── Camera ─────────────────────────────────────────────────────────────
    const W = containerRef.current.clientWidth;
    const camera = new THREE.PerspectiveCamera(45, W / VIEWER_HEIGHT, 0.001, 2000);

    // ── Renderer ───────────────────────────────────────────────────────────
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(W, VIEWER_HEIGHT);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    containerRef.current.innerHTML = '';
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // ── Lights ─────────────────────────────────────────────────────────────
    scene.add(new THREE.AmbientLight(0xffffff, 1.0));
    scene.add(new THREE.HemisphereLight(0xffffff, 0x1d2433, 0.9));

    const keyLight  = new THREE.DirectionalLight(0xffffff, 1.8);
    keyLight.castShadow = true;
    scene.add(keyLight);
    const fillLight = new THREE.DirectionalLight(0xe6eefc, 1.0);
    scene.add(fillLight);
    const backLight = new THREE.DirectionalLight(0xffffff, 0.6);
    scene.add(backLight);
    const lights = { key: keyLight, fill: fillLight, back: backLight };

    // ── Grid ───────────────────────────────────────────────────────────────
    scene.add(new THREE.GridHelper(10, 10, 0x444444, 0x222222));

    // ── Controls ───────────────────────────────────────────────────────────
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping    = true;
    controls.dampingFactor    = 0.05;
    controls.minDistance      = 0.1;
    controls.maxDistance      = 50;
    controls.screenSpacePanning = true;

    // ── Build mesh from inline data ────────────────────────────────────────
    try {
      const geo = buildGeometry(meshData);
      const mat = new THREE.MeshStandardMaterial({
        color:     0xd4b896,
        roughness: 0.65,
        metalness: 0.05,
        side:      THREE.DoubleSide,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.castShadow    = true;
      mesh.receiveShadow = true;
      mesh.frustumCulled = false;

      // Bake centering into geometry (feet at Y=0, X/Z centred, facing camera)
      centreAtOrigin(mesh);

      scene.add(mesh);
      meshRef.current = mesh;

      // Frame camera after geometry is finalised
      frameCamera(camera, controls, mesh, lights);

      setIsReady(true);
    } catch (err) {
      console.error('SMPLViewer build error:', err);
      setLoadError(err?.message || 'Failed to build mesh');
      return;
    }

    // ── Render loop ────────────────────────────────────────────────────────
    let rafId;
    const animate = () => {
      if (disposed) return;
      rafId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // ── Resize ─────────────────────────────────────────────────────────────
    const onResize = () => {
      if (!containerRef.current) return;
      const w = containerRef.current.clientWidth;
      camera.aspect = w / VIEWER_HEIGHT;
      camera.updateProjectionMatrix();
      renderer.setSize(w, VIEWER_HEIGHT);
    };
    window.addEventListener('resize', onResize);

    return () => {
      disposed = true;
      window.removeEventListener('resize', onResize);
      cancelAnimationFrame(rafId);
      controls.dispose();
      disposeMesh(meshRef.current);
      meshRef.current = null;
      renderer.dispose();
      scene.clear();
    };
  }, [meshData]);

  // ── Empty state ───────────────────────────────────────────────────────────
  if (!meshData?.x?.length) {
    return (
      <div style={{
        background: '#1a1a2e', borderRadius: 12, overflow: 'hidden',
        border: '1px solid #333', height: VIEWER_HEIGHT,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#9ba3b4', fontSize: 14,
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ marginBottom: 8 }}>3D model not available</div>
          <div style={{ fontSize: 12, color: '#6b7280' }}>
            Ensure SMPL processing completed successfully
          </div>
        </div>
      </div>
    );
  }

  const metadata           = meshData.metadata || {};
  const fittedToUser       = Boolean(metadata.fitted_to_user);
  const poseApplied        = Boolean(metadata.pose_applied);
  const viewerStatusText   = statusText   || metadata.status_text || (fittedToUser ? '✓ Model fitted to your body' : '3D model ready');
  const viewerStatusDetail = statusDetail || (poseApplied ? 'Pose matched to your image · Interactive 3D viewer' : 'Neutral pose · Interactive 3D viewer');

  return (
    <div style={{ background: '#1a1a2e', borderRadius: 12, overflow: 'hidden', border: '1px solid #333' }}>
      <div style={{
        padding: '12px 16px', borderBottom: '1px solid #333',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ color: '#fff', fontWeight: 600, fontSize: 14 }}>3D BODY MODEL</span>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
          <span style={{ color: fittedToUser ? '#86efac' : '#9ba3b4', fontSize: 12, fontWeight: 600 }}>
            {viewerStatusText}
          </span>
          <span style={{ color: loadError ? '#fca5a5' : isReady ? '#86efac' : '#9ba3b4', fontSize: 12 }}>
            {loadError || (isReady ? viewerStatusDetail : 'Building 3D mesh...')}
          </span>
          <span style={{ color: '#9ba3b4', fontSize: 12 }}>
            Left-click to rotate · Right-click to pan · Scroll to zoom
          </span>
        </div>
      </div>
      <div ref={containerRef} style={{ width: '100%', height: VIEWER_HEIGHT }} />
    </div>
  );
};

export default SMPLViewer;
