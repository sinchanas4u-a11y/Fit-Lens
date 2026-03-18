import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Paper,
  Tab,
  Tabs,
  TextField,
  Typography
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import Webcam from 'react-webcam';
import io from 'socket.io-client';

const VIEW_ORDER = ['front', 'right', 'back', 'left'];

function LiveMode({ onBack }) {
  const webcamRef = useRef(null);
  const socketRef = useRef(null);
  const processingIndexRef = useRef(0);

  const [connected, setConnected] = useState(false);
  const [sessionStarted, setSessionStarted] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState(null);

  const [userHeight, setUserHeight] = useState('170');
  const [heightUnit, setHeightUnit] = useState('cm');

  const [currentView, setCurrentView] = useState('front');
  const [alignment, setAlignment] = useState('red');
  const [instruction, setInstruction] = useState('Align your full body in frame');
  const [countdown, setCountdown] = useState(null);

  const [capturedImages, setCapturedImages] = useState({});
  const [isReviewing, setIsReviewing] = useState(false);

  const [processing, setProcessing] = useState(false);
  const [processingIndex, setProcessingIndex] = useState(0);
  const [processErrors, setProcessErrors] = useState({});
  const [resultsPayload, setResultsPayload] = useState(null);
  const [selectedTab, setSelectedTab] = useState('front');

  useEffect(() => {
    processingIndexRef.current = processingIndex;
  }, [processingIndex]);

  const connectedViews = useMemo(
    () => VIEW_ORDER.filter((v) => Boolean(capturedImages[v])),
    [capturedImages]
  );

  useEffect(() => {
    const socket = io('http://localhost:5001');
    socketRef.current = socket;

    socket.on('connect', () => {
      setConnected(true);
      setInstruction('Connected. Start session to begin capture.');
    });

    socket.on('disconnect', () => {
      setConnected(false);
      setInstruction('Disconnected from backend.');
    });

    socket.on('frame_processed', (data) => {
      setAlignment(data.alignment || 'red');
      setInstruction(data.instruction || 'Adjust your position.');
      setCountdown(data.countdown ?? null);
    });

    socket.on('capture_complete', (data) => {
      const view = data.view;
      const nextView = data.next_view;
      const image = data.image;

      if (view && image) {
        setCapturedImages((prev) => ({ ...prev, [view]: image }));
      }

      if (nextView && nextView !== 'complete') {
        setCurrentView(nextView);
      } else if (nextView === 'complete') {
        setIsReviewing(true);
      }
    });

    socket.on('selection_processed', (data) => {
      const current = processingIndexRef.current;

      if (data?.error) {
        const failedView = VIEW_ORDER[current] || 'unknown';
        setProcessErrors((prev) => ({ ...prev, [failedView]: data.error }));
      }

      const nextIndex = current + 1;
      if (nextIndex < VIEW_ORDER.length) {
        setProcessingIndex(nextIndex);
      } else {
        socket.emit('finalize_session');
      }
    });

    socket.on('processing_complete', (payload) => {
      setResultsPayload(payload);
      setSelectedTab('front');
      setProcessing(false);
    });

    socket.on('error', (err) => {
      setProcessing(false);
      setInstruction(err?.message || 'Live processing error');
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  useEffect(() => {
    if (!processing) {
      return;
    }

    const activeView = VIEW_ORDER[processingIndex];
    const imageData = capturedImages[activeView];

    if (!activeView || !imageData || !socketRef.current) {
      return;
    }

    socketRef.current.emit('process_selection', {
      view: activeView,
      image: imageData,
      type: 'auto',
      user_height: Number(userHeight),
      height_unit: heightUnit
    });
  }, [processing, processingIndex, capturedImages, userHeight, heightUnit]);

  useEffect(() => {
    if (!sessionStarted || isReviewing || processing || resultsPayload || !connected) {
      return;
    }

    const interval = setInterval(() => {
      if (!webcamRef.current || !socketRef.current) {
        return;
      }

      const frame = webcamRef.current.getScreenshot();
      if (!frame) {
        return;
      }

      socketRef.current.emit('process_frame', {
        image: frame,
        view: currentView,
        user_height: Number(userHeight),
        height_unit: heightUnit
      });
    }, 220);

    return () => clearInterval(interval);
  }, [sessionStarted, isReviewing, processing, resultsPayload, connected, currentView, userHeight, heightUnit]);

  const resetSession = useCallback(() => {
    setSessionStarted(false);
    setCameraReady(false);
    setCameraError(null);
    setCurrentView('front');
    setAlignment('red');
    setInstruction('Align your full body in frame');
    setCountdown(null);
    setCapturedImages({});
    setIsReviewing(false);
    setProcessing(false);
    setProcessingIndex(0);
    setProcessErrors({});
    setResultsPayload(null);
    setSelectedTab('front');
    if (socketRef.current) {
      socketRef.current.emit('reset_session');
    }
  }, []);

  const startSession = () => {
    if (!Number(userHeight) || Number(userHeight) <= 0) {
      setInstruction('Enter a valid height to continue.');
      return;
    }

    setSessionStarted(true);
    setIsReviewing(false);
    setResultsPayload(null);
    setProcessErrors({});
    setInstruction('Front view: stand straight, full body visible.');
  };

  const manualCapture = () => {
    if (!webcamRef.current) {
      return;
    }
    const frame = webcamRef.current.getScreenshot();
    if (!frame) {
      return;
    }

    setCapturedImages((prev) => ({ ...prev, [currentView]: frame }));
    const currentIndex = VIEW_ORDER.indexOf(currentView);
    if (currentIndex < VIEW_ORDER.length - 1) {
      setCurrentView(VIEW_ORDER[currentIndex + 1]);
      setInstruction('Capture complete. Rotate to next view.');
    } else {
      setIsReviewing(true);
      setInstruction('All views captured. Review and process measurements.');
    }
  };

  const retakeView = (view) => {
    setCapturedImages((prev) => {
      const next = { ...prev };
      delete next[view];
      return next;
    });
    setCurrentView(view);
    setIsReviewing(false);
    setResultsPayload(null);
    setProcessErrors((prev) => {
      const next = { ...prev };
      delete next[view];
      return next;
    });
    if (socketRef.current) {
      socketRef.current.emit('retake_view', { view });
    }
  };

  const processMeasurements = () => {
    const missing = VIEW_ORDER.filter((v) => !capturedImages[v]);
    if (missing.length > 0) {
      setInstruction(`Please capture all 4 views. Missing: ${missing.join(', ')}`);
      return;
    }

    setProcessing(true);
    setProcessingIndex(0);
    setProcessErrors({});
    setInstruction('Processing all views using height-based pixel-to-scale conversion...');
  };

  const renderMeasurementsTable = (measurements) => {
    const entries = Object.entries(measurements || {});
    if (entries.length === 0) {
      return <Typography variant="body2">No measurements available for this view.</Typography>;
    }

    return (
      <div className="live-results-table-wrap">
        <table className="live-results-table">
          <thead>
            <tr>
              <th>Measurement</th>
              <th>Value (cm)</th>
              <th>Value (px)</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([name, data]) => (
              <tr key={name}>
                <td>{name.replace(/_/g, ' ').toUpperCase()}</td>
                <td>{Number(data.value_cm || 0).toFixed(2)}</td>
                <td>{Number(data.value_px || 0).toFixed(2)}</td>
                <td>{`${Math.round(Number(data.confidence || 0) * 100)}%`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderPerViewPanels = (viewKey) => {
    const viewData = resultsPayload?.results?.[viewKey] || {};

    return (
      <div className="live-panels-grid">
        <Paper className="live-result-panel" sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Original</Typography>
          <img
            className="live-result-image"
            src={viewData.original_image || capturedImages[viewKey]}
            alt={`${viewKey} original`}
          />
        </Paper>

        <Paper className="live-result-panel" sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Segmentation Mask</Typography>
          <img
            className="live-result-image live-mask-image"
            src={viewData.mask}
            alt={`${viewKey} segmentation mask`}
          />
          <Typography variant="caption" color="text.secondary">
            White silhouette on black background (same upload-mode mask style).
          </Typography>
        </Paper>

        <Paper className="live-result-panel" sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Landmark Detection Overlay</Typography>
          <img
            className="live-result-image"
            src={viewData.visualization}
            alt={`${viewKey} landmark overlay`}
          />
        </Paper>

        <Paper className="live-result-panel" sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Measurements</Typography>
          {renderMeasurementsTable(viewData.measurements)}
        </Paper>
      </div>
    );
  };

  const renderAllMeasurements = () => {
    const rows = [];
    VIEW_ORDER.forEach((view) => {
      const measurements = resultsPayload?.results?.[view]?.measurements || {};
      Object.entries(measurements).forEach(([name, data]) => {
        rows.push({
          view,
          name,
          cm: Number(data.value_cm || 0),
          px: Number(data.value_px || 0),
          confidence: Number(data.confidence || 0)
        });
      });
    });

    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>All Measurements</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Pixel-to-scale formula used for all 4 photos: user height (cm) / detected body height (px).
        </Typography>
        <div className="live-results-table-wrap">
          <table className="live-results-table">
            <thead>
              <tr>
                <th>View</th>
                <th>Measurement</th>
                <th>Value (cm)</th>
                <th>Value (px)</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={`${row.view}-${row.name}-${idx}`}>
                  <td>{row.view.toUpperCase()}</td>
                  <td>{row.name.replace(/_/g, ' ').toUpperCase()}</td>
                  <td>{row.cm.toFixed(2)}</td>
                  <td>{row.px.toFixed(2)}</td>
                  <td>{`${Math.round(row.confidence * 100)}%`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Paper>
    );
  };

  if (resultsPayload) {
    const calibration = resultsPayload.calibration || {};

    return (
      <div className="live-container">
        <Button startIcon={<ArrowBackIcon />} onClick={onBack} sx={{ mb: 2 }}>
          Back to Dashboard
        </Button>

        <Typography variant="h4" gutterBottom>Live Camera Results</Typography>

        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1">Height-Based Pixel-to-Scale Calibration</Typography>
          <Typography variant="body2" color="text.secondary">
            User height: {Number(calibration.user_height_cm || 0).toFixed(2)} cm
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Scale factor: {Number(calibration.scale_factor || 0).toFixed(6)} cm/px
          </Typography>
        </Paper>

        <Paper sx={{ p: 1, mb: 2 }}>
          <Tabs
            value={selectedTab}
            onChange={(_, v) => setSelectedTab(v)}
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab label="Front" value="front" />
            <Tab label="Right" value="right" />
            <Tab label="Back" value="back" />
            <Tab label="Left" value="left" />
            <Tab label="All Measurements" value="all" />
          </Tabs>
        </Paper>

        {selectedTab === 'all' ? renderAllMeasurements() : renderPerViewPanels(selectedTab)}

        <Box sx={{ mt: 2 }}>
          <Button variant="outlined" onClick={resetSession}>Start New Session</Button>
        </Box>
      </div>
    );
  }

  if (isReviewing) {
    return (
      <div className="live-container">
        <Button startIcon={<ArrowBackIcon />} onClick={onBack} sx={{ mb: 2 }}>
          Back to Dashboard
        </Button>

        <Typography variant="h4" gutterBottom>Review Captured Views</Typography>
        <div className="live-review-grid">
          {VIEW_ORDER.map((view) => (
            <Paper key={view} sx={{ p: 1 }}>
              <Typography variant="subtitle2" gutterBottom>{view.toUpperCase()}</Typography>
              <img className="live-review-thumb" src={capturedImages[view]} alt={`${view} capture`} />
              <Button size="small" sx={{ mt: 1 }} onClick={() => retakeView(view)}>
                Retake
              </Button>
            </Paper>
          ))}
        </div>

        {Object.keys(processErrors).length > 0 && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            {Object.entries(processErrors).map(([view, msg]) => `${view}: ${msg}`).join(' | ')}
          </Alert>
        )}

        <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
          <Button variant="contained" onClick={processMeasurements} disabled={processing}>
            {processing ? `Processing ${processingIndex + 1}/4...` : 'Process Measurements'}
          </Button>
          <Button variant="outlined" onClick={resetSession}>Restart Session</Button>
        </Box>
      </div>
    );
  }

  return (
    <div className="live-container">
      <Button startIcon={<ArrowBackIcon />} onClick={onBack} sx={{ mb: 2 }}>
        Back to Dashboard
      </Button>

      <Typography variant="h4" gutterBottom>Live Camera Mode</Typography>

      <div className="live-grid">
        <div className="live-controls">
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Setup</Typography>
            <TextField
              label="Height"
              type="number"
              fullWidth
              margin="normal"
              value={userHeight}
              onChange={(e) => setUserHeight(e.target.value)}
            />
            <TextField
              label="Unit (cm/inches/feet)"
              fullWidth
              margin="normal"
              value={heightUnit}
              onChange={(e) => setHeightUnit(e.target.value)}
            />
            <Button variant="contained" fullWidth sx={{ mt: 1 }} onClick={startSession} disabled={!connected}>
              Start Session
            </Button>
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Status</Typography>
            <div className={`status-indicator status-${alignment}`}>
              {alignment === 'green' ? 'Aligned' : 'Adjust Position'}
            </div>
            <Typography variant="body2" sx={{ mt: 1 }}>{instruction}</Typography>
            {countdown !== null && countdown >= 0 && <div className="countdown">{countdown}</div>}
            <Typography variant="body2" color="text.secondary">
              Current view: {currentView.toUpperCase()} ({connectedViews.length}/4 captured)
            </Typography>
          </Paper>

          {cameraError && <Alert severity="error">{cameraError}</Alert>}
          {!connected && <Alert severity="warning">Backend not connected (`http://localhost:5001`).</Alert>}
        </div>

        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Camera Feed</Typography>
          <div className="camera-feed live-webcam-box">
            <Webcam
              ref={webcamRef}
              audio={false}
              screenshotFormat="image/jpeg"
              onUserMedia={() => {
                setCameraReady(true);
                setCameraError(null);
              }}
              onUserMediaError={(err) => {
                setCameraReady(false);
                setCameraError(err?.message || 'Unable to access camera');
              }}
              videoConstraints={{ facingMode: 'user' }}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>

          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button variant="contained" onClick={manualCapture} disabled={!sessionStarted || !cameraReady}>
              Capture {currentView.toUpperCase()}
            </Button>
            <Button variant="outlined" onClick={resetSession}>Reset</Button>
          </Box>
        </Paper>
      </div>
    </div>
  );
}

export default LiveMode;
