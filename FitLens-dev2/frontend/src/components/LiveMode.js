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
  Box,
  Alert,
  Checkbox
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import VideocamIcon from '@mui/icons-material/Videocam';
import PhotoCameraIcon from '@mui/icons-material/PhotoCamera';
import axios from 'axios';
import io from 'socket.io-client';

function LiveMode({ onBack }) {
  const [socket, setSocket] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [referenceSize, setReferenceSize] = useState('29.7');
  const [referenceAxis, setReferenceAxis] = useState('height');
  const [referenceCaptured, setReferenceCaptured] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [status, setStatus] = useState('Not Ready');
  const [statusColor, setStatusColor] = useState('red');
  const [countdown, setCountdown] = useState(null);
  const [feedback, setFeedback] = useState([]);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [error, setError] = useState(null);
  
  const canvasRef = useRef(null);

  useEffect(() => {
    // Initialize socket connection
    console.log('Connecting to WebSocket...');
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);

    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      addFeedback('Connected to server');
    });

    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      addFeedback('Disconnected from server');
    });

    newSocket.on('camera_frame', (data) => {
      console.log('Received camera frame');
      setCurrentFrame(data.frame);
      
      // Update status based on alignment
      if (data.alignment) {
        const statusTexts = {
          'red': '🔴 Adjust Position',
          'amber': '🟡 Almost Ready',
          'green': '🟢 Perfect! Hold Still'
        };
        setStatus(statusTexts[data.alignment] || 'Not Ready');
        setStatusColor(data.alignment);
      }
      
      // Update countdown
      if (data.countdown !== null && data.countdown !== undefined) {
        setCountdown(data.countdown);
      } else {
        setCountdown(null);
      }
      
      // Update feedback for object detection
      if (data.has_object === false && referenceCaptured) {
        addFeedback('Please hold the reference object in your hand');
      }
    });

    newSocket.on('auto_capture', (data) => {
      if (data.success) {
        addFeedback('✓ Measurement captured automatically!');
        if (voiceEnabled) {
          speak('Measurement captured');
        }
        // Display results
        if (data.result && data.result.measurements) {
          displayMeasurements(data.result.measurements, data.result.scale_info);
        }
      }
    });

    return () => {
      newSocket.close();
      stopCamera();
    };
  }, [referenceCaptured, voiceEnabled]);

  useEffect(() => {
    if (currentFrame && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const img = new Image();
      img.onload = () => {
        // Set canvas size to match container
        const container = canvas.parentElement;
        const maxWidth = container.clientWidth;
        const maxHeight = container.clientHeight || 600;
        
        // Calculate aspect ratio
        const aspectRatio = img.width / img.height;
        let drawWidth = maxWidth;
        let drawHeight = maxWidth / aspectRatio;
        
        if (drawHeight > maxHeight) {
          drawHeight = maxHeight;
          drawWidth = maxHeight * aspectRatio;
        }
        
        canvas.width = drawWidth;
        canvas.height = drawHeight;
        ctx.drawImage(img, 0, 0, drawWidth, drawHeight);
      };
      img.onerror = () => {
        console.error('Failed to load image');
      };
      img.src = `data:image/jpeg;base64,${currentFrame}`;
    }
  }, [currentFrame]);

  const startCamera = async () => {
    try {
      console.log('Starting camera...');
      const response = await axios.post('/api/camera/start');
      console.log('Camera started:', response.data);
      setCameraActive(true);
      setError(null);
      addFeedback('Camera started successfully');
    } catch (err) {
      console.error('Failed to start camera:', err);
      setError('Failed to start camera: ' + (err.response?.data?.error || err.message));
      addFeedback('ERROR: Failed to start camera');
    }
  };

  const stopCamera = async () => {
    try {
      await axios.post('/api/camera/stop');
      setCameraActive(false);
    } catch (err) {
      console.error('Failed to stop camera:', err);
    }
  };

  const captureReference = async () => {
    try {
      const response = await axios.post('/api/camera/capture-reference', {
        reference_size: parseFloat(referenceSize),
        reference_axis: referenceAxis
      });

      setReferenceCaptured(true);
      setStatus('Reference Captured');
      setStatusColor('amber');
      
      // Display calibration info
      addFeedback('✓ Reference object captured successfully!');
      addFeedback('');
      addFeedback('=== CALIBRATION INFO ===');
      addFeedback(`Reference: ${referenceSize} cm`);
      addFeedback(`Detected: ${response.data.reference_px.toFixed(2)} pixels`);
      addFeedback(`Scale Factor: ${response.data.scale_factor.toFixed(4)} cm/px`);
      addFeedback(`Formula: ${referenceSize} ÷ ${response.data.reference_px.toFixed(2)} = ${response.data.scale_factor.toFixed(4)}`);
      addFeedback('');
      addFeedback('Now hold the object and align your body for measurement.');
      
      if (voiceEnabled) {
        speak('Reference captured');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to capture reference');
      if (voiceEnabled) {
        speak('Reference not found');
      }
    }
  };

  const displayMeasurements = (measurements, scaleInfo) => {
    addFeedback('=== PIXEL-TO-SCALE CALIBRATION ===');
    if (scaleInfo) {
      addFeedback(`Scale Factor: ${scaleInfo.scale_factor.toFixed(4)} ${scaleInfo.unit}`);
      addFeedback(`${scaleInfo.description}`);
    }
    addFeedback('');
    addFeedback('=== MEASUREMENTS ===');
    Object.entries(measurements).forEach(([name, data]) => {
      const displayName = name.replace(/_/g, ' ').toUpperCase();
      if (data.value_pixels) {
        addFeedback(`${displayName}:`);
        addFeedback(`  ${data.value_pixels.toFixed(0)} px → ${data.value_cm.toFixed(2)} cm`);
        addFeedback(`  Confidence: ${(data.confidence * 100).toFixed(0)}%`);
      } else {
        addFeedback(`${displayName}: ${data.value_cm?.toFixed(2) || data.value?.toFixed(2)} cm (${(data.confidence * 100).toFixed(0)}%)`);
      }
    });
  };

  const addFeedback = (message) => {
    setFeedback(prev => [
      `[${new Date().toLocaleTimeString()}] ${message}`,
      ...prev.slice(0, 9)
    ]);
  };

  const speak = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleBack = () => {
    stopCamera();
    onBack();
  };

  useEffect(() => {
    if (!cameraActive) {
      startCamera();
    }
  }, []);

  return (
    <div className="live-container">
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={handleBack}
        sx={{ mb: 2 }}
      >
        Back to Dashboard
      </Button>

      <Typography variant="h4" gutterBottom>
        Live Camera Mode
      </Typography>

      <div className="live-grid">
        <div className="live-controls">
          <Paper sx={{ p: 2 }}>
            <div className={`status-indicator status-${statusColor}`}>
              {status}
            </div>
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Step 1: Capture Reference
            </Typography>

            <TextField
              label="Size (cm)"
              type="number"
              value={referenceSize}
              onChange={(e) => setReferenceSize(e.target.value)}
              fullWidth
              margin="normal"
              size="small"
            />

            <FormControl component="fieldset" margin="normal">
              <FormLabel component="legend">Axis</FormLabel>
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
              fullWidth
              startIcon={<PhotoCameraIcon />}
              onClick={captureReference}
              disabled={!cameraActive}
              sx={{ mt: 2 }}
            >
              Capture Reference
            </Button>
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Step 2: Align & Capture
            </Typography>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Hold the reference object in your hand and align your body with the template.
              Auto-capture will trigger after 3 seconds of perfect alignment.
            </Typography>

            {countdown !== null && countdown >= 0 && (
              <div className="countdown">
                {countdown}
              </div>
            )}

            {!referenceCaptured && (
              <Alert severity="info" sx={{ mt: 2 }}>
                Please capture reference object first
              </Alert>
            )}

            {referenceCaptured && (
              <Alert severity="success" sx={{ mt: 2 }}>
                ✓ Reference captured. Hold object in hand and align your body.
              </Alert>
            )}
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Feedback
            </Typography>

            <div className="feedback-box">
              {feedback.map((msg, idx) => (
                <Typography key={idx} variant="body2" sx={{ mb: 1 }}>
                  {msg}
                </Typography>
              ))}
            </div>

            <FormControlLabel
              control={
                <Checkbox
                  checked={voiceEnabled}
                  onChange={(e) => setVoiceEnabled(e.target.checked)}
                />
              }
              label="Voice Guidance"
              sx={{ mt: 2 }}
            />
          </Paper>

          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
        </div>

        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Camera Feed
          </Typography>
          
          <div className="camera-feed" style={{ 
            minHeight: '480px', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            background: '#000'
          }}>
            {currentFrame ? (
              <canvas 
                ref={canvasRef} 
                style={{ 
                  maxWidth: '100%', 
                  maxHeight: '600px',
                  display: 'block'
                }} 
              />
            ) : (
              <Typography variant="body1" color="text.secondary">
                Starting camera...
              </Typography>
            )}
          </div>

          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              🔴 Red: Adjust position | 🟡 Amber: Almost ready | 🟢 Green: Perfect!
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              💡 Hold the reference object in your hand for auto-capture
            </Typography>
          </Box>
        </Paper>
      </div>
    </div>
  );
}

export default LiveMode;
