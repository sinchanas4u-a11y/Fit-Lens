import Plot from 'react-plotly.js';

const SMPLViewer = ({ meshData, statusText, statusDetail }) => {
  // Debug logging
  console.log('🔍 SMPLViewer - meshData received:', meshData);
  if (meshData) {
    console.log('📊 meshData.x length:', meshData.x?.length);
    console.log('📊 meshData.y length:', meshData.y?.length);
    console.log('📊 meshData.z length:', meshData.z?.length);
    console.log('📊 meshData.i length:', meshData.i?.length);
    console.log('📊 meshData.j length:', meshData.j?.length);
    console.log('📊 meshData.k length:', meshData.k?.length);
  }

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

  const data = [
    {
      type: 'mesh3d',
      x: meshData.x,
      y: meshData.y,
      z: meshData.z,
      i: meshData.i,
      j: meshData.j,
      k: meshData.k,
      color: '#e8b89a',
      opacity: 1.0,
      flatshading: false,
      lighting: {
        ambient: 0.7,
        diffuse: 0.8,
        specular: 0.3,
        roughness: 0.5,
        fresnel: 0.2,
      },
      lightposition: {
        x: 100,
        y: 200,
        z: 150,
      },
    },
  ];

  const layout = {
    paper_bgcolor: '#1a1a2e',
    plot_bgcolor: '#1a1a2e',
    height: 500,
    margin: { l: 0, r: 0, t: 0, b: 0 },
    scene: {
      bgcolor: '#1a1a2e',
      aspectmode: 'data',
      camera: {
        eye: { x: 0, y: 0.5, z: 2.5 },
      },
      xaxis: {
        showgrid: false,
        zeroline: false,
        showticklabels: false,
        showbackground: false,
      },
      yaxis: {
        showgrid: false,
        zeroline: false,
        showticklabels: false,
        showbackground: false,
      },
      zaxis: {
        showgrid: false,
        zeroline: false,
        showticklabels: false,
        showbackground: false,
      },
    },
  };

  const config = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['toImage', 'sendDataToCloud'],
  };

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
            Drag to rotate · Scroll to zoom · Double-click to reset
          </span>
        </div>
      </div>

      <Plot
        data={data}
        layout={layout}
        config={config}
        style={{ width: '100%' }}
        useResizeHandler={true}
      />
    </div>
  );
};

export default SMPLViewer;
