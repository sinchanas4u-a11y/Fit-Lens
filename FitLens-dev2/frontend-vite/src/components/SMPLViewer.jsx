import { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader';

const VIEWER_HEIGHT = 500;

const resolveMeshResource = (meshData) => {
  const metadata = meshData?.metadata || {};
  const backendUrl = metadata.mesh_url || meshData?.mesh_url || null;
  const sessionId = meshData?.session_id || metadata.session_id || '';
  const fallbackUrl = sessionId
    ? `/mesh/${sessionId}/front/000.obj`
    : '/mesh/front/000.obj';
  const meshUrl = `${backendUrl || fallbackUrl}?v=${Date.now()}`;
  const explicitFormat = (metadata.mesh_format || '').toLowerCase();
  const extensionMatch = meshUrl.match(/\.([a-z0-9]+)(?:\?|$)/i);
  const meshFormat = explicitFormat || extensionMatch?.[1]?.toLowerCase() || 'obj';

  return {
    meshUrl,
    meshFormat,
    sessionId,
    backendUrl: backendUrl || fallbackUrl,
    meshFileExists: metadata.mesh_file_exists,
    meshFilePath: metadata.mesh_file_path || null,
  };
};

const createLoader = (meshFormat) => {
  if (meshFormat === 'gltf' || meshFormat === 'glb') {
    return new GLTFLoader();
  }

  return new OBJLoader();
};

const normalizeLoadedObject = (loadedAsset) => {
  if (loadedAsset?.scene) {
    return loadedAsset.scene;
  }

  return loadedAsset;
};

const applyVisibleMaterial = (material) => {
  const baseMaterial = material?.isMaterial ? material.clone() : new THREE.MeshStandardMaterial();

  if (baseMaterial.color == null) {
    baseMaterial.color = new THREE.Color(0xd9b08c);
  }

  baseMaterial.side = THREE.DoubleSide;
  baseMaterial.transparent = false;
  baseMaterial.opacity = 1;
  baseMaterial.depthWrite = true;
  baseMaterial.needsUpdate = true;
  return baseMaterial;
};

const prepareRenderableObject = (rootObject) => {
  let meshCount = 0;

  rootObject.traverse((child) => {
    if (!(child instanceof THREE.Mesh)) {
      return;
    }

    meshCount += 1;
    child.visible = true;
    child.frustumCulled = false;
    child.castShadow = true;
    child.receiveShadow = true;

    if (child.geometry) {
      child.geometry.computeBoundingBox();
      child.geometry.computeVertexNormals();
    }

    if (Array.isArray(child.material)) {
      child.material = child.material.length > 0
        ? child.material.map((material) => applyVisibleMaterial(material))
        : [applyVisibleMaterial(null)];
      return;
    }

    child.material = applyVisibleMaterial(child.material);
  });

  return meshCount;
};

const frameCameraToObject = (camera, controls, object, lights) => {
  const box = new THREE.Box3().setFromObject(object);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z, 0.1);
  const fov = THREE.MathUtils.degToRad(camera.fov);
  const distance = (maxDim / (2 * Math.tan(fov / 2))) * 1.5;

  // Target mid-torso (~55% of height from feet = box.min.y)
  const target = new THREE.Vector3(center.x, box.min.y + size.y * 0.55, center.z);

  camera.near = Math.max(0.01, distance / 100);
  camera.far = Math.max(1000, distance * 20);
  camera.position.set(center.x, target.y, target.z + distance);
  camera.lookAt(target);
  camera.updateProjectionMatrix();

  if (controls) {
    controls.target.copy(target);
    controls.update();
  }

  if (lights) {
    lights.key.position.set(distance, distance * 1.2, distance);
    lights.fill.position.set(-distance * 0.8, distance * 0.5, distance * 0.6);
    lights.back.position.set(0, distance * 0.7, -distance);
  }

  return { box, size, center: target, distance };
};

const disposeSceneObject = (object) => {
  object?.traverse((child) => {
    if (child.geometry) {
      child.geometry.dispose();
    }

    if (Array.isArray(child.material)) {
      child.material.forEach((material) => material?.dispose?.());
      return;
    }

    child.material?.dispose?.();
  });
};

const SMPLViewer = ({ meshData, statusText, statusDetail }) => {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const meshRef = useRef(null);
  const [isReady, setIsReady] = useState(false);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    if (!containerRef.current || !meshData) return;

    setIsReady(false);
    setLoadError(null);

    let isDisposed = false;

    // Initialize Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#1a1a2e');
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, containerRef.current.clientWidth / VIEWER_HEIGHT, 0.01, 2000);
    camera.position.set(0, 1.25, 3.5);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(containerRef.current.clientWidth, VIEWER_HEIGHT);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    containerRef.current.innerHTML = '';
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.1);
    scene.add(ambientLight);

    const hemisphereLight = new THREE.HemisphereLight(0xffffff, 0x1d2433, 1.1);
    hemisphereLight.position.set(0, 12, 0);
    scene.add(hemisphereLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.8);
    keyLight.position.set(5, 10, 7);
    keyLight.castShadow = true;
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xe6eefc, 1.0);
    fillLight.position.set(-5, 5, 6);
    scene.add(fillLight);

    const backLight = new THREE.DirectionalLight(0xffffff, 0.7);
    backLight.position.set(0, 4, -6);
    scene.add(backLight);

    const lights = {
      key: keyLight,
      fill: fillLight,
      back: backLight,
    };

    // Helpers to debug scene
    const grid = new THREE.GridHelper(10, 10, 0x444444, 0x222222);
    scene.add(grid);
    const axes = new THREE.AxesHelper(1.5);
    scene.add(axes);

    const { meshUrl, meshFormat, sessionId, backendUrl, meshFileExists, meshFilePath } = resolveMeshResource(meshData);
    console.log('🔍 Backend mesh path:', backendUrl);
    console.log('🧾 Mesh metadata:', {
      sessionId: sessionId || 'none',
      meshFormat,
      meshFileExists,
      meshFilePath,
    });

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 0.1;
    controls.maxDistance = 50;
    controls.screenSpacePanning = true;

    const verifyMeshFile = async () => {
      const response = await fetch(meshUrl, { method: 'HEAD' });
      if (!response.ok) {
        throw new Error(`Mesh request failed with ${response.status} ${response.statusText}`);
      }
      console.log(`✅ Mesh file exists: ${backendUrl}`);
    };

    const loadMesh = () => {
      const loader = createLoader(meshFormat);
      console.log(`📦 Using ${meshFormat.toUpperCase()} loader for ${backendUrl}`);

      loader.load(
        meshUrl,
        (loadedAsset) => {
          if (isDisposed) {
            return;
          }

          const object = normalizeLoadedObject(loadedAsset);
          const meshCount = prepareRenderableObject(object);
          console.log('✅ SMPL mesh loaded successfully');
          console.log(`📦 Mesh count: ${meshCount}`);

          if (meshCount === 0) {
            console.warn('⚠️ No renderable meshes found in loaded asset');
          }

          const initialBox = new THREE.Box3().setFromObject(object);
          if (initialBox.isEmpty()) {
            setLoadError('Loaded mesh has empty bounds');
            return;
          }

          // Center the object dynamically
          const initialCenter = initialBox.getCenter(new THREE.Vector3());
          // Center X and Z, and place the bottom (feet) at Y = 0
          object.position.set(-initialCenter.x, -initialBox.min.y, -initialCenter.z);
          
          // Apply changes before framing
          object.updateMatrixWorld();

          scene.add(object);
          meshRef.current = object;

          const framed = frameCameraToObject(camera, controls, object, lights);
          console.log('✅ Mesh loaded:', {
            vertices: object.children?.[0]?.geometry?.attributes?.position?.count,
            size: framed.size,
            distance: framed.distance,
          });

          setIsReady(true);
        },
        (xhr) => {
          if (xhr.total > 0) {
            const progress = (xhr.loaded / xhr.total * 100).toFixed(0);
            if (progress === '25' || progress === '50' || progress === '75' || progress === '100') {
              console.log(`📥 Model ${progress}% loaded`);
            }
          }
        },
        (error) => {
          console.error('❌ Error loading SMPL model from URL:', backendUrl, error);
          setLoadError(error?.message || 'Failed to load mesh');
        }
      );
    };

    verifyMeshFile()
      .then(() => {
        if (!isDisposed) {
          loadMesh();
        }
      })
      .catch((error) => {
        console.error('❌ Mesh file verification failed:', backendUrl, error);
        setLoadError(error?.message || 'Mesh file verification failed');
      });

    // Animation loop
    let requestID;
    let loggedRenderLoop = false;
    const animate = () => {
      if (isDisposed) {
        return;
      }
      requestID = requestAnimationFrame(animate);
      if (!loggedRenderLoop) {
        console.log('🔄 Render loop active');
        loggedRenderLoop = true;
      }
      controls.update();
      renderer.render(scene, camera);
    };
    console.log('🎬 Starting SMPL viewer render loop');
    animate();

    // Resize handler
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current) return;
      const width = containerRef.current.clientWidth;
      camera.aspect = width / VIEWER_HEIGHT;
      camera.updateProjectionMatrix();
      renderer.setSize(width, VIEWER_HEIGHT);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      isDisposed = true;
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(requestID);
      controls.dispose();
      disposeSceneObject(meshRef.current);
      meshRef.current = null;
      renderer.dispose();
      scene.clear();
    };
  }, [meshData, meshData?.session_id]);

  if (!meshData || !meshData.x || meshData.x.length === 0) {
    return (
      <div
        style={{
          background: '#1a1a2e',
          borderRadius: 12,
          overflow: 'hidden',
          border: '1px solid #333',
          height: 500,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#9ba3b4',
          fontSize: 14,
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div style={{ marginBottom: 8 }}>3D model not available</div>
          <div style={{ fontSize: 12, color: '#6b7280' }}>
            Ensure SMPL processing completed successfully
          </div>
        </div>
      </div>
    );
  }

  const metadata = meshData.metadata || {};
  const fittedToUser = Boolean(metadata.fitted_to_user);
  const poseApplied = Boolean(metadata.pose_applied);
  const viewerStatusText = statusText || metadata.status_text || (fittedToUser ? '✓ Model fitted to your body' : '3D model ready');
  const viewerStatusDetail = statusDetail || (poseApplied ? 'Pose matched to your image · Interactive 3D viewer' : 'Neutral pose · Interactive 3D viewer');

  return (
    <div
      style={{
        background: '#1a1a2e',
        borderRadius: 12,
        overflow: 'hidden',
        border: '1px solid #333',
      }}
    >
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid #333',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span
          style={{
            color: '#fff',
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          3D BODY MODEL
        </span>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
          <span
            style={{
              color: fittedToUser ? '#86efac' : '#9ba3b4',
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            {viewerStatusText}
          </span>
          <span
            style={{
              color: loadError ? '#fca5a5' : isReady ? '#86efac' : '#9ba3b4',
              fontSize: 12,
            }}
          >
            {loadError || (isReady ? viewerStatusDetail : 'Loading and framing mesh...')}
          </span>
          <span
            style={{
              color: '#9ba3b4',
              fontSize: 12,
            }}
          >
            Left-click to rotate · Right-click to pan · Scroll to zoom
          </span>
        </div>
      </div>

      <div ref={containerRef} style={{ width: '100%', height: 500 }} />
    </div>
  );
};

export default SMPLViewer;
