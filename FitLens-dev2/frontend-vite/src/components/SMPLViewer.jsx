import { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader';

const SMPLViewer = ({ meshData, statusText, statusDetail }) => {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const meshRef = useRef(null);
  const [isReady, setIsReady] = useState(false);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    if (!containerRef.current || !meshData) return;

    // Initialize Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#1a1a2e');
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, containerRef.current.clientWidth / 500, 0.1, 1000);
    camera.position.set(0, 1, 3);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(containerRef.current.clientWidth, 500);
    renderer.setPixelRatio(window.devicePixelRatio);
    containerRef.current.innerHTML = '';
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const mainLight = new THREE.DirectionalLight(0xffffff, 1.0);
    mainLight.position.set(2, 4, 6);
    scene.add(mainLight);

    // Load OBJ Mesh
    const loader = new OBJLoader();
    const meshUrl = '/mesh/front/000.obj';
    
    loader.load(
      meshUrl,
      (object) => {
        object.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            child.material = new THREE.MeshStandardMaterial({
              color: 0xe8b89a,
              roughness: 0.6,
              metalness: 0.1,
              flatShading: false,
              side: THREE.DoubleSide,
            });
            
            // Auto-center and fit
            child.geometry.computeBoundingBox();
            const center = new THREE.Vector3();
            child.geometry.boundingBox.getCenter(center);
            child.position.sub(center);
          }
        });
        
        // Ensure strictly upright (usually standard for OBJ export from SMPL)
        // If it needs rotation (e.g. from Z-up to Y-up), we apply it here.
        // For now, assume Y-up.
        
        scene.add(object);
        meshRef.current = object;
        setIsReady(true);
      },
      (xhr) => {
        console.log(`Model ${(xhr.loaded / xhr.total * 100)}% loaded`);
      },
      (error) => {
        console.error('An error happened while loading the model:', error);
        setLoadError(true);
      }
    );

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Animation loop
    let requestID;
    const animate = () => {
      requestID = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Resize handler
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current) return;
      const width = containerRef.current.clientWidth;
      camera.aspect = width / 500;
      camera.updateProjectionMatrix();
      renderer.setSize(width, 500);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(requestID);
      renderer.dispose();
      // Materials and geometries should be disposed too but object.traverse is better
    };
  }, [meshData]);

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
  const viewerStatusText = statusText || metadata.status_text || (fittedToUser ? '✓ Model fitted to your body' : '3D model ready');
  const viewerStatusDetail = statusDetail || (metadata.pose_applied ? 'Real MediaPipe landmarks and body pose applied' : 'Interactive viewer ready');

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
              color: '#9ba3b4',
              fontSize: 12,
            }}
          >
            {viewerStatusDetail}
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
