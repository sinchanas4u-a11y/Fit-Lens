import React, { useState } from 'react';
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
  const [error, setError] = useState(null);

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
