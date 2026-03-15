import React, { useState, useEffect, useRef } from 'react';
import {
  Typography,
  Button,
  TextField,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import axios from 'axios';

function UploadMode({ onBack }) {
  const [referenceSize, setReferenceSize] = useState('29.7');
  const [referenceAxis, setReferenceAxis] = useState('height');
  const [images, setImages] = useState({
    reference: null,
    front: null,
    side: null
  });
  const [previews, setPreviews] = useState({});
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [meshData, setMeshData] = useState(null);
  const [modelStatus, setModelStatus] = useState('');
  const [show3DModel] = useState(true); // Always show 3D model when available
  const plotlyRef = useRef(null);
  const [error, setError] = useState(null);

  const normalizeMeshData = (rawMesh) => {
    if (!rawMesh) return null;

    if (rawMesh.x && rawMesh.y && rawMesh.z && rawMesh.i && rawMesh.j && rawMesh.k) {
      return rawMesh;
    }

    if (Array.isArray(rawMesh.vertices) && Array.isArray(rawMesh.faces)) {
      const vertices = rawMesh.vertices;
      const faces = rawMesh.faces;
      if (vertices.length % 3 !== 0 || faces.length % 3 !== 0) {
        return null;
      }

      const x = [];
      const y = [];
      const z = [];
      for (let n = 0; n < vertices.length; n += 3) {
        x.push(vertices[n]);
        y.push(vertices[n + 1]);
        z.push(vertices[n + 2]);
      }

      const i = [];
      const j = [];
      const k = [];
      for (let n = 0; n < faces.length; n += 3) {
        i.push(faces[n]);
        j.push(faces[n + 1]);
        k.push(faces[n + 2]);
      }

      return {
        x,
        y,
        z,
        i,
        j,
        k,
        metadata: rawMesh.metadata || {}
      };
    }

    return null;
  };

  useEffect(() => {
    if (!window.Plotly) {
      const script = document.createElement('script');
      script.src = 'https://cdn.plot.ly/plotly-2.27.0.min.js';
      script.async = true;
      document.head.appendChild(script);
    }
  }, []);

  useEffect(() => {
    if (!meshData) return;

    let retryTimer = null;
    let renderTimer = null;
    let plottedDiv = null;

    const tryRender = () => {
      const div = plotlyRef.current;
      if (!div) return;
      if (!window.Plotly) {
        retryTimer = setTimeout(tryRender, 500);
        return;
      }

      plottedDiv = div;

      window.Plotly.newPlot(div, [{
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
          fresnel: 0.2
        },
        lightposition: {
          x: 100, y: 200, z: 150
        }
      }], {
        paper_bgcolor: '#1a1a2e',
        margin: { l: 0, r: 0, t: 0, b: 0 },
        scene: {
          bgcolor: '#1a1a2e',
          aspectmode: 'data',
          camera: {
            eye: { x: 0.0, y: 0.3, z: 2.2 },
            up: { x: 0, y: 1, z: 0 }
          },
          xaxis: {
            visible: false,
            showgrid: false,
            showbackground: false
          },
          yaxis: {
            visible: false,
            showgrid: false,
            showbackground: false
          },
          zaxis: {
            visible: false,
            showgrid: false,
            showbackground: false
          }
        }
      }, {
        responsive: true,
        displaylogo: false
      });

      const src = meshData.metadata?.source || 'SMPL';
      const h = meshData.metadata?.height_cm || '';
      const fitted = meshData.metadata?.betas_fitted;
      setModelStatus(
        `${fitted
          ? '✓ Model fitted to your body'
          : '3D model generated'
        } · ${src}${h ? ` · Height: ${h}cm` : ''}`
      );
      console.log('3D model rendered OK');
    };

    renderTimer = setTimeout(tryRender, 300);

    return () => {
      if (retryTimer) {
        clearTimeout(retryTimer);
      }
      if (renderTimer) {
        clearTimeout(renderTimer);
      }

      if (plottedDiv && window.Plotly) {
        window.Plotly.purge(plottedDiv);
      }
    };
  }, [meshData]);

  const handleImageUpload = (type, event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImages(prev => ({ ...prev, [type]: reader.result }));
        setPreviews(prev => ({ ...prev, [type]: reader.result }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleProcess = async () => {
    if (!images.reference || !images.front) {
      setError('Please upload at least reference and front images');
      return;
    }

    setProcessing(true);
    setError(null);

    try {
      const response = await axios.post('/api/upload/process', {
        reference_image: images.reference,
        front_image: images.front,
        side_image: images.side,
        reference_size: parseFloat(referenceSize),
        reference_axis: referenceAxis
      });

      setResults(response.data);
      console.log('Full API response keys:', Object.keys(response.data));
      console.log('mesh_data present:', !!response.data.mesh_data);
      console.log('mesh_data x length:', response.data.mesh_data?.x?.length);
      const rawMesh = response.data.mesh_data || response.data.results?.front?.mesh_data;
      const normalizedMesh = normalizeMeshData(rawMesh);

      if (normalizedMesh &&
          normalizedMesh.x &&
          normalizedMesh.x.length > 0) {
        setMeshData(normalizedMesh);
        console.log('mesh_data received:',
          normalizedMesh.x.length,
          'vertices');
      } else {
        console.log('No mesh_data in response');
        setMeshData(null);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Processing failed');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="upload-container">
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={onBack}
        sx={{ mb: 2 }}
      >
        Back to Dashboard
      </Button>

      <Typography variant="h4" gutterBottom>
        Upload Images Mode
      </Typography>

      <div className="upload-grid">
        <div className="upload-controls">
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Reference Object
            </Typography>
            
            <TextField
              label="Known Size (cm)"
              type="number"
              value={referenceSize}
              onChange={(e) => setReferenceSize(e.target.value)}
              fullWidth
              margin="normal"
              helperText="e.g., 29.7 for A4 height"
            />

            <FormControl component="fieldset" margin="normal">
              <FormLabel component="legend">Measurement Axis</FormLabel>
              <RadioGroup
                value={referenceAxis}
                onChange={(e) => setReferenceAxis(e.target.value)}
                row
              >
                <FormControlLabel value="width" control={<Radio />} label="Width" />
                <FormControlLabel value="height" control={<Radio />} label="Height" />
              </RadioGroup>
            </FormControl>

            <Button
              variant="contained"
              component="label"
              fullWidth
              startIcon={<CloudUploadIcon />}
              sx={{ mt: 2 }}
            >
              Upload Reference Image
              <input
                type="file"
                hidden
                accept="image/*"
                onChange={(e) => handleImageUpload('reference', e)}
              />
            </Button>

            <Button
              variant="contained"
              component="label"
              fullWidth
              startIcon={<CloudUploadIcon />}
              sx={{ mt: 2 }}
            >
              Upload Front View
              <input
                type="file"
                hidden
                accept="image/*"
                onChange={(e) => handleImageUpload('front', e)}
              />
            </Button>

            <Button
              variant="contained"
              component="label"
              fullWidth
              startIcon={<CloudUploadIcon />}
              sx={{ mt: 2 }}
            >
              Upload Side View (Optional)
              <input
                type="file"
                hidden
                accept="image/*"
                onChange={(e) => handleImageUpload('side', e)}
              />
            </Button>

            <Button
              variant="contained"
              color="primary"
              fullWidth
              onClick={handleProcess}
              disabled={processing || !images.reference || !images.front}
              sx={{ mt: 3 }}
            >
              {processing ? <CircularProgress size={24} /> : 'Process & Measure'}
            </Button>
          </Paper>
        </div>

        <div>
          {Object.keys(previews).length > 0 && (
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Preview
              </Typography>
              {Object.entries(previews).map(([type, preview]) => (
                <div key={type}>
                  <Typography variant="subtitle2" gutterBottom>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </Typography>
                  <img src={preview} alt={type} className="image-preview" />
                </div>
              ))}
            </Paper>
          )}

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {results && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Results
              </Typography>
              
              {/* Calibration Information */}
              {results.calibration && (
                <Paper sx={{ p: 2, mb: 2, bgcolor: 'primary.dark' }}>
                  <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                    📏 Pixel-to-Scale Calibration
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Reference Object:</strong> {results.calibration.reference_size_cm} cm = {results.calibration.reference_size_px.toFixed(2)} pixels
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Formula:</strong> {results.calibration.formula}
                  </Typography>
                  <Typography variant="body2" gutterBottom sx={{ color: 'success.main' }}>
                    <strong>Scale Factor:</strong> {results.calibration.scale_factor.toFixed(4)} cm/pixel
                  </Typography>
                  <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                    {results.calibration.description}
                  </Typography>
                </Paper>
              )}

              {results.results?.front && (
                <>
                  <Typography variant="subtitle1" sx={{ mt: 2 }}>
                    Front View Measurements
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Measurement</TableCell>
                          <TableCell align="right">Pixels</TableCell>
                          <TableCell align="right">Centimeters</TableCell>
                          <TableCell align="right">Confidence</TableCell>
                          <TableCell>Calculation</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(results.results.front.measurements || {}).map(([name, data]) => (
                          <TableRow key={name}>
                            <TableCell>{name.replace(/_/g, ' ')}</TableCell>
                            <TableCell align="right">{data.value_pixels?.toFixed(0) || 'N/A'} px</TableCell>
                            <TableCell align="right" sx={{ fontWeight: 'bold' }}>{data.value_cm?.toFixed(2)} cm</TableCell>
                            <TableCell align="right">{(data.confidence * 100).toFixed(0)}%</TableCell>
                            <TableCell sx={{ fontSize: '0.75rem' }}>{data.calculation || 'N/A'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {/* Scale Information */}
                  {results.results.front.scale_info && (
                    <Alert severity="info" sx={{ mt: 2 }}>
                      <strong>Scale Info:</strong> {results.results.front.scale_info.description}
                    </Alert>
                  )}

                  {results.results.front.visualization && (
                    <div>
                      <Typography variant="subtitle2" sx={{ mt: 2 }}>
                        Visualization with Measurements
                      </Typography>
                      <img
                        src={results.results.front.visualization}
                        alt="visualization"
                        className="image-preview"
                      />
                    </div>
                  )}

                  {/* 3D Body Model - Hidden via React state and CSS display: none */}
                  <div style={{
                    marginTop: '24px',
                    display: (meshData && show3DModel) ? 'block' : 'none'
                  }}>
                    <div style={{
                      background:'#1a1a2e',
                      borderRadius:'12px',
                      overflow:'hidden',
                      border:'1px solid #333'
                    }}>
                      <div style={{
                        padding:'12px 16px',
                        color:'#fff',
                        fontWeight:'600',
                        fontSize:'14px',
                        borderBottom:'1px solid #333',
                        display:'flex',
                        justifyContent:'space-between',
                        alignItems:'center'
                      }}>
                        <span>3D BODY MODEL</span>
                        <span style={{
                          color:'#888',
                          fontSize:'12px',
                          fontWeight:'400'
                        }}>
                          Drag to rotate · Scroll to zoom
                        </span>
                      </div>

                      <div
                        id="smpl-3d-viewer"
                        ref={plotlyRef}
                        style={{
                          width:'100%',
                          height:'520px',
                          background:'#1a1a2e'
                        }}
                      />

                      <div style={{
                        textAlign:'center',
                        padding:'8px',
                        fontSize:'12px',
                        color:'#888',
                        borderTop:'1px solid #333'
                      }}>
                        {modelStatus || 'Loading 3D model...'}
                      </div>
                    </div>
                  </div>
                </>
              )}
            </Paper>
          )}
        </div>
      </div>
    </div>
  );
}

export default UploadMode;
