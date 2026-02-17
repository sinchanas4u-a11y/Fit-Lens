import { useState, useEffect } from 'react';
import axios from 'axios';
import './UploadMode.css';
import ModeSelection from './ModeSelection';
import ManualLandmarkMarker from './ManualLandmarkMarker';

const UploadMode = () => {
  const [frontImage, setFrontImage] = useState(null);
  const [sideImage, setSideImage] = useState(null);

  const [frontPreview, setFrontPreview] = useState(null);
  const [sidePreview, setSidePreview] = useState(null);

  const [userHeight, setUserHeight] = useState('');
  const [heightUnit, setHeightUnit] = useState('cm');

  const [processing, setProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // New states for mode selection and manual marking
  const [showModeSelection, setShowModeSelection] = useState(false);
  const [selectedMode, setSelectedMode] = useState(null);
  const [showManualMarker, setShowManualMarker] = useState(false);
  const [currentMarkingView, setCurrentMarkingView] = useState(null);
  const [manualLandmarks, setManualLandmarks] = useState({
    front: null,
    side: null
  });

  // New states for face verification
  const [isVerifying, setIsVerifying] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  const [verificationError, setVerificationError] = useState(null);
  const [verificationIssues, setVerificationIssues] = useState({ front: [], side: [] }); // New: detailed issues

  const steps = [
    'Upload Photos',
    'Verify Identity', // Added verification step
    'Calculate Scale from Height',
    'YOLOv8 Segmentation',
    'MediaPipe Landmarks',
    'Compute Measurements',
    'Display Results'
  ];

  // Effect to trigger verification when both images are present
  useEffect(() => {
    if (frontImage && sideImage && !isVerified && !isVerifying) {
      handleIdentityVerification();
    }
  }, [frontImage, sideImage]);

  const handleIdentityVerification = async () => {
    setIsVerifying(true);
    setIsVerifying(true);
    setVerificationError(null);
    setVerificationIssues({ front: [], side: [] }); // Reset issues
    setIsVerified(false);

    try {
      console.log('👤 Starting identity verification (with resizing)...');
      const frontBase64 = await resizeImage(frontImage);
      const sideBase64 = await resizeImage(sideImage);

      const response = await axios.post('/api/verify-identity', {
        front_image: frontBase64,
        side_image: sideBase64
      }, {
        timeout: 60000 // 60s timeout for axios
      });

      if (response.data.success && response.data.verified) {
        console.log('✓ Identity verified successfully');
        setIsVerified(true);
        // Do NOT show issues if verified, as per requirements
        setVerificationIssues({ front: [], side: [] });
      } else {
        const errorMsg = response.data.message || response.data.error || 'Face verification failed.';
        const issues = response.data.issues || { front: [], side: [] };
        console.error('✗ Verification failed:', errorMsg);
        setVerificationError(errorMsg);
        setVerificationIssues(issues);
      }
    } catch (err) {
      console.error('❌ Verification API error:', err);
      const status = err.response?.status;
      const apiError = err.response?.data?.error || err.response?.data?.message;
      let message = apiError || 'Face verification failed. Please upload front and side images of the same person.';
      if (status === 503) {
        message = 'Face verification service unavailable. Please try again later or continue without a side image.';
      }
      setVerificationError(message);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleImageUpload = (e, setImage, setPreview) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setImage(file);
      setIsVerified(false); // Reset verification if images change
      setVerificationError(null);
      setVerificationIssues({ front: [], side: [] }); // Clear issues on new upload
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const resizeImage = (file, maxWidth = 800, maxHeight = 800) => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          let width = img.width;
          let height = img.height;

          if (width > height) {
            if (width > maxWidth) {
              height *= maxWidth / width;
              width = maxWidth;
            }
          } else {
            if (height > maxHeight) {
              width *= maxHeight / height;
              height = maxHeight;
            }
          }

          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);
          resolve(canvas.toDataURL('image/jpeg', 0.8)); // Compress as JPEG
        };
        img.src = e.target.result;
      };
      reader.readAsDataURL(file);
    });
  };

  const imageToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleInitialProcess = async () => {
    // Validation
    if (!frontImage) {
      setError('Please upload a front view image');
      return;
    }

    if (!userHeight) {
      setError('Please enter your height');
      return;
    }

    // Show mode selection dialog
    setShowModeSelection(true);
  };

  const handleModeSelection = (mode) => {
    setSelectedMode(mode);
    setShowModeSelection(false);

    if (mode === 'manual') {
      // Start manual marking with front image
      setCurrentMarkingView('front');
      setShowManualMarker(true);
    } else {
      // Start automatic processing
      handleAutomaticProcess();
    }
  };

  const handleManualLandmarkComplete = (data) => {
    // Save landmarks for current view
    setManualLandmarks(prev => ({
      ...prev,
      [currentMarkingView]: data
    }));

    setShowManualMarker(false);

    // If side image exists and hasn't been marked yet, mark it
    if (sideImage && currentMarkingView === 'front' && !manualLandmarks.side) {
      setTimeout(() => {
        setCurrentMarkingView('side');
        setShowManualMarker(true);
      }, 100);
    } else {
      // Process with manual landmarks
      processManualLandmarks({
        ...manualLandmarks,
        [currentMarkingView]: data
      });
    }
  };

  const handleManualMarkingCancel = () => {
    setShowManualMarker(false);
    setCurrentMarkingView(null);
    setSelectedMode(null);
    // Reset and show mode selection again
    setShowModeSelection(true);
  };

  const processManualLandmarks = async (landmarks) => {
    setProcessing(true);
    setError(null);
    setResults(null);

    try {
      console.log('🎯 Processing manual landmarks...', landmarks);

      // Convert height to cm if needed
      let heightInCm = parseFloat(userHeight);
      if (heightUnit === 'inches') {
        heightInCm = heightInCm * 2.54;
      } else if (heightUnit === 'feet') {
        heightInCm = heightInCm * 30.48;
      }

      const requestData = {
        user_height: heightInCm,
        front_landmarks: landmarks.front || null,
        side_landmarks: landmarks.side || null,
        front_image: frontImage ? await imageToBase64(frontImage) : null,
        side_image: sideImage ? await imageToBase64(sideImage) : null
      };

      console.log('📤 Sending manual landmarks to backend:', {
        ...requestData,
        front_image: requestData.front_image ? '(base64 data)' : null,
        side_image: requestData.side_image ? '(base64 data)' : null
      });

      const response = await axios.post('/api/process-manual', requestData, {
        timeout: 120000
      });

      console.log('📥 Received response from backend:', response.data);

      setResults(response.data);
      setProcessing(false);

    } catch (err) {
      console.error('❌ Manual processing error:', err);
      const status = err.response?.status;
      const apiError = err.response?.data?.error || err.response?.data?.message;
      let message = apiError || 'Manual processing failed. Please try again.';
      if (status === 503) {
        message = 'Processing service unavailable. Please try again in a moment.';
      }
      setError(message);
      setProcessing(false);
    }
  };

  const handleAutomaticProcess = async () => {
    setProcessing(true);
    setError(null);
    setResults(null);
    setCurrentStep(0);

    try {
      console.log('🚀 Starting automatic image processing...');

      // Step 1: Upload Photos
      setCurrentStep(1);
      await new Promise(resolve => setTimeout(resolve, 500));

      console.log('📸 Converting images to base64...');
      const frontBase64 = await imageToBase64(frontImage);
      const sideBase64 = sideImage ? await imageToBase64(sideImage) : null;
      console.log('✓ Images converted');

      // Convert height to cm if needed
      let heightInCm = parseFloat(userHeight);
      if (heightUnit === 'inches') {
        heightInCm = heightInCm * 2.54;
      } else if (heightUnit === 'feet') {
        heightInCm = heightInCm * 30.48;
      }

      const requestData = {
        front_image: frontBase64,
        side_image: sideBase64,
        user_height: heightInCm
      };

      console.log('📤 Sending request to backend:', {
        has_front: !!requestData.front_image,
        has_side: !!requestData.side_image,
        user_height: requestData.user_height,
        height_unit: heightUnit
      });

      // Send to backend
      const response = await axios.post('/api/process', requestData, {
        timeout: 120000
      });

      console.log('📥 Received response from backend');
      console.log('Response data:', JSON.stringify(response.data, null, 2));

      // Check if we have measurements
      if (response.data.results?.front?.measurements) {
        const measurementCount = Object.keys(response.data.results.front.measurements).length;
        console.log(`✓ Found ${measurementCount} measurements in front view`);
        console.log('Measurements:', response.data.results.front.measurements);
      } else {
        console.warn('⚠️ No measurements found in response!');
        console.log('Response structure:', {
          has_results: !!response.data.results,
          has_front: !!response.data.results?.front,
          has_measurements: !!response.data.results?.front?.measurements,
          front_keys: response.data.results?.front ? Object.keys(response.data.results.front) : []
        });
      }

      // Simulate step progression
      // Step 2 was Verify Identity (already done)
      for (let step = 3; step <= 7; step++) {
        setCurrentStep(step);
        await new Promise(resolve => setTimeout(resolve, 800));
      }

      console.log('✓ Processing complete, setting results');
      setResults(response.data);
      setProcessing(false);

    } catch (err) {
      console.error('❌ Processing error:', err);
      console.error('Error details:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status
      });
      const status = err.response?.status;
      const step = err.response?.data?.step;
      const apiError = err.response?.data?.error || err.response?.data?.message;
      let message = apiError || 'Processing failed. Please try again.';
      if (status === 503 && step === 1.5) {
        message = 'Face verification service unavailable. Please try again later or remove the side image.';
      } else if (status === 400 && step === 1.5) {
        message = apiError || 'Face verification failed. Please upload front and side images of the same person.';
      }
      setError(message);
      setProcessing(false);
      setCurrentStep(0);
    }
  };

  const handleProcess = handleInitialProcess;

  const handleReset = () => {
    setFrontImage(null);
    setSideImage(null);
    setFrontPreview(null);
    setSidePreview(null);
    setUserHeight('');
    setResults(null);
    setError(null);
    setCurrentStep(0);
    setShowModeSelection(false);
    setSelectedMode(null);
    setShowManualMarker(false);
    setCurrentMarkingView(null);
    setManualLandmarks({ front: null, side: null });
    setIsVerified(false);
    setIsVerifying(false);
    setVerificationError(null);
  };

  const downloadJSON = () => {
    // Sanitize results to remove confidence scores for export
    const sanitizedResults = JSON.parse(JSON.stringify(results));
    if (sanitizedResults.results) {
      ['front', 'side'].forEach(view => {
        if (sanitizedResults.results[view]?.measurements) {
          Object.values(sanitizedResults.results[view].measurements).forEach(m => {
            delete m.confidence;
          });
        }
      });
    }
    const dataStr = JSON.stringify(sanitizedResults, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'measurements.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="upload-mode">
      <h2>Body Measurement - Upload Mode</h2>

      {/* Progress Steps */}
      {processing && (
        <div className="progress-steps">
          {steps.map((step, index) => (
            <div
              key={index}
              className={`step ${currentStep > index ? 'completed' : ''} ${currentStep === index + 1 ? 'active' : ''}`}
            >
              <div className="step-number">{index + 1}</div>
              <div className="step-label">{step}</div>
            </div>
          ))}
        </div>
      )}

      {!results ? (
        <div className="upload-section">
          {/* Image Upload Section */}
          <div className="upload-grid">
            {/* Front Image */}
            <div className="upload-box">
              <h3>Front View *</h3>
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>
                Stand straight, full body visible, arms slightly away from body
              </p>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => handleImageUpload(e, setFrontImage, setFrontPreview)}
                disabled={processing}
              />
              {frontPreview && (
                <div className="image-preview">
                  <img src={frontPreview} alt="Front view" />
                </div>
              )}
              {/* Front Image Error Display */}
              {verificationIssues?.front && verificationIssues.front.length > 0 && (
                <div style={{ marginTop: '5px', padding: '8px', background: '#fff1f0', border: '1px solid #ffa39e', borderRadius: '4px', color: '#cf1322', fontSize: '13px' }}>
                  <strong>Issues:</strong>
                  <ul style={{ margin: '5px 0 0 20px', padding: 0 }}>
                    {verificationIssues.front.map((issue, i) => (
                      <li key={i}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Side Image */}
            <div className="upload-box">
              <h3>Side View (Optional)</h3>
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>
                Side profile, full body visible
              </p>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => handleImageUpload(e, setSideImage, setSidePreview)}
                disabled={processing}
              />
              {sidePreview && (
                <div className="image-preview">
                  <img src={sidePreview} alt="Side view" />
                </div>
              )}
              {/* Side Image Error Display */}
              {verificationIssues?.side && verificationIssues.side.length > 0 && (
                <div style={{ marginTop: '5px', padding: '8px', background: '#fff1f0', border: '1px solid #ffa39e', borderRadius: '4px', color: '#cf1322', fontSize: '13px' }}>
                  <strong>Issues:</strong>
                  <ul style={{ margin: '5px 0 0 20px', padding: 0 }}>
                    {verificationIssues.side.map((issue, i) => (
                      <li key={i}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Identity Verification Status */}
          {(isVerifying || verificationError || (frontImage && sideImage && isVerified)) && (
            <div className={`verification-status ${verificationError ? 'error' : isVerified ? 'success' : 'pending'}`}
              style={{
                margin: '20px 0',
                padding: '15px',
                borderRadius: '8px',
                backgroundColor: verificationError ? '#fff1f0' : isVerified ? '#f6ffed' : '#e6f7ff',
                border: `1px solid ${verificationError ? '#ffa39e' : isVerified ? '#b7eb8f' : '#91d5ff'}`
              }}>
              {isVerifying ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div className="spinner" style={{
                    width: '20px',
                    height: '20px',
                    border: '3px solid #f3f3f3',
                    borderTop: '3px solid #1890ff',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                  <span>Verifying identity... Please wait.</span>
                </div>
              ) : verificationError ? (
                <div style={{ color: '#cf1322', fontWeight: 'bold' }}>
                  ⚠️ {verificationError}
                </div>
              ) : isVerified ? (
                <div style={{ color: '#389e0d', fontWeight: 'bold' }}>
                  ✅ Identity verified! You can now proceed.
                </div>
              ) : null}
            </div>
          )}

          {/* User Height Input - Only show if verified */}
          {isVerified && (
            <div className="reference-inputs">
              <h3>Your Height *</h3>
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '15px' }}>
                Enter your actual height for accurate measurements
              </p>
              <div className="input-group">
                <label style={{ flex: 2 }}>
                  Height:
                  <input
                    type="number"
                    step="0.1"
                    value={userHeight}
                    onChange={(e) => setUserHeight(e.target.value)}
                    placeholder="e.g., 170"
                    disabled={processing}
                    style={{ fontSize: '18px', padding: '12px' }}
                  />
                </label>
                <label style={{ flex: 1 }}>
                  Unit:
                  <select
                    value={heightUnit}
                    onChange={(e) => setHeightUnit(e.target.value)}
                    disabled={processing}
                    style={{ fontSize: '16px', padding: '12px' }}
                  >
                    <option value="cm">cm</option>
                    <option value="inches">inches</option>
                    <option value="feet">feet</option>
                  </select>
                </label>
              </div>
              <p className="hint">
                Examples: 170 cm, 5.6 feet, or 67 inches
              </p>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="error-message">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Process Button - Only show if verified */}
          {isVerified && (
            <button
              className="process-button"
              onClick={handleProcess}
              disabled={processing || !frontImage || !userHeight}
            >
              {processing ? 'Processing...' : 'Process Images'}
            </button>
          )}
        </div>
      ) : (
        <div className="results-section">
          <h2>
            Measurement Results
            {results.mode && (
              <span style={{
                fontSize: '16px',
                marginLeft: '10px',
                padding: '4px 12px',
                background: results.mode === 'manual' ? '#ff9800' : '#4caf50',
                color: 'white',
                borderRadius: '12px',
                fontWeight: 'normal'
              }}>
                {results.mode === 'manual' ? '✋ Manual Mode' : '🤖 Automatic Mode'}
              </span>
            )}
          </h2>

          {/* Manual Mode Note */}
          {results.mode === 'manual' && (
            <div style={{
              background: '#fff3cd',
              border: '1px solid #ff9800',
              padding: '12px',
              borderRadius: '5px',
              marginBottom: '20px'
            }}>
              <strong>ℹ️ Manual Mode:</strong> Showing only the measurements you marked manually.
            </div>
          )}

          {/* Debug: Show full response */}
          <details style={{ marginBottom: '20px', padding: '10px', background: '#f0f0f0', borderRadius: '5px' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>🔍 Debug: View Raw Response Data</summary>
            <pre style={{ overflow: 'auto', maxHeight: '300px', fontSize: '12px' }}>
              {JSON.stringify(results, null, 2)}
            </pre>
          </details>

          {/* Calibration Info */}
          <div className="calibration-info">
            <h3>Height-Based Calibration</h3>
            <p><strong>Your Height:</strong> {results.calibration.user_height_cm} cm</p>
            <p><strong>Height in Image:</strong> {results.calibration.height_in_image_px.toFixed(2)} pixels</p>
            <p><strong>Scale Factor:</strong> {results.calibration.scale_factor.toFixed(4)} cm/px</p>
            <p className="formula">{results.calibration.formula}</p>
            <p style={{ fontSize: '14px', marginTop: '10px', fontStyle: 'italic' }}>
              {results.calibration.description}
            </p>
          </div>

          {/* Debug Info */}
          {console.log('🔍 Rendering results:', {
            has_results: !!results,
            has_results_obj: !!results?.results,
            mode: results?.mode,
            has_merged: !!results?.results?.merged,
            has_front: !!results?.results?.front,
            front_success: results?.results?.front?.success,
            has_measurements: !!results?.results?.front?.measurements,
            measurement_count: results?.results?.front?.measurements ? Object.keys(results.results.front.measurements).length : 0
          })}

          {/* MANUAL MODE: Consolidated Single Table */}
          {results.mode === 'manual' && results.results.merged && results.results.merged.success && (
            <div className="view-results">
              <h3>Consolidated Body Measurements</h3>
              <p style={{
                color: '#ff9800',
                fontSize: '14px',
                fontStyle: 'italic',
                marginBottom: '15px'
              }}>
                ✋ Manual Mode: Displaying arm length from side view and leg length from front view
              </p>

              {/* Visualizations - Show both Front and Side */}
              <div className="visualizations">
                {/* Front View Visualization and Mask */}
                {results.results.merged.front_visualization && (
                  <>
                    <div className="vis-item">
                      <h4>Front View - Marked Landmarks</h4>
                      <img src={results.results.merged.front_visualization} alt="Front view landmarks" />
                    </div>
                    {results.results.merged.front_mask && (
                      <div className="vis-item">
                        <h4>Front View - Segmentation Mask</h4>
                        <img src={results.results.merged.front_mask} alt="Front mask" />
                      </div>
                    )}
                  </>
                )}

                {/* Side View Visualization and Mask */}
                {results.results.merged.side_visualization && (
                  <>
                    <div className="vis-item">
                      <h4>Side View - Marked Landmarks</h4>
                      <img src={results.results.merged.side_visualization} alt="Side view landmarks" />
                    </div>
                    {results.results.merged.side_mask && (
                      <div className="vis-item">
                        <h4>Side View - Segmentation Mask</h4>
                        <img src={results.results.merged.side_mask} alt="Side mask" />
                      </div>
                    )}
                  </>
                )}

                {/* Fallback to legacy fields if new fields not available */}
                {!results.results.merged.front_visualization && !results.results.merged.side_visualization && results.results.merged.visualization && (
                  <>
                    <div className="vis-item">
                      <h4>Marked Landmarks</h4>
                      <img src={results.results.merged.visualization} alt="Manual landmarks" />
                    </div>
                    {results.results.merged.mask && (
                      <div className="vis-item">
                        <h4>Segmentation Mask</h4>
                        <img src={results.results.merged.mask} alt="Segmentation mask" />
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Consolidated Measurements Table */}
              <div className="measurements-table">
                <h4>Body Measurements ({results.results.merged.measurements ? Object.keys(results.results.merged.measurements).length : 0} measurements)</h4>

                {!results.results.merged.measurements || Object.keys(results.results.merged.measurements).length === 0 ? (
                  <div className="error-message">
                    <strong>Debug:</strong> No measurements found in merged result.
                    <pre>{JSON.stringify(results.results.merged, null, 2)}</pre>
                  </div>
                ) : (
                  <>
                    {/* Simple list view as fallback */}
                    <div style={{ marginBottom: '20px', padding: '15px', background: '#f9f9f9', borderRadius: '5px' }}>
                      <h5>Measurements List:</h5>
                      {Object.entries(results.results.merged.measurements).map(([name, data]) => (
                        <div key={name} style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>
                          <strong>{name.replace(/_/g, ' ').toUpperCase()}:</strong>{' '}
                          {data.value_cm} cm ({data.value_px.toFixed(2)} px)
                          {data.label && <span style={{ color: '#666', marginLeft: '10px' }}>({data.label})</span>}
                          {/* Show view source for arm_length and leg_length */}
                          {name === 'arm_length' && <span style={{ color: '#2196f3', marginLeft: '10px', fontWeight: 'bold' }}>[Side View]</span>}
                          {name === 'leg_length' && <span style={{ color: '#4caf50', marginLeft: '10px', fontWeight: 'bold' }}>[Front View]</span>}
                        </div>
                      ))}
                    </div>

                    {/* Table view */}
                    <table>
                      <thead>
                        <tr>
                          <th>Measurement</th>
                          <th>Value (cm)</th>
                          <th>Value (px)</th>
                          <th>View</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(results.results.merged.measurements).map(([name, data]) => {
                          console.log(`📏 Rendering merged measurement: ${name}`, data);
                          // Determine which view the measurement came from
                          let viewBadge = data.source || 'Manual';
                          if (name === 'arm_length') {
                            viewBadge = 'Side View';
                          } else if (name === 'leg_length') {
                            viewBadge = 'Front View';
                          }

                          return (
                            <tr key={name}>
                              <td>{data.label || name.replace(/_/g, ' ').toUpperCase()}</td>
                              <td>{data.value_cm} cm</td>
                              <td>{data.value_px.toFixed(2)} px</td>
                              <td style={{
                                fontSize: '12px',
                                fontWeight: (name === 'arm_length' || name === 'leg_length') ? 'bold' : 'normal',
                                color: name === 'arm_length' ? '#2196f3' : (name === 'leg_length' ? '#4caf50' : '#666')
                              }}>
                                {viewBadge}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </>
                )}
              </div>
            </div>
          )}

          {/* AUTOMATIC MODE: Separate Front and Side Tables */}
          {results.mode !== 'manual' && results.results.front && results.results.front.success && (
            <div className="view-results">
              <h3>Front View Measurements</h3>

              {/* Debug: Show raw data */}
              {console.log('📊 Front measurements:', results.results.front.measurements)}

              {/* Visualizations */}
              <div className="visualizations">
                <div className="vis-item">
                  <h4>Landmarks</h4>
                  <img src={results.results.front.visualization} alt="Front landmarks" />
                </div>
                <div className="vis-item">
                  <h4>Segmentation Mask</h4>
                  <img src={results.results.front.mask} alt="Front mask" />
                </div>
              </div>

              {/* Measurements Table */}
              <div className="measurements-table">
                <h4>Body Measurements ({results.results.front.measurements ? Object.keys(results.results.front.measurements).length : 0} measurements)</h4>

                {/* Debug: Check if measurements exist */}
                {!results.results.front.measurements || Object.keys(results.results.front.measurements).length === 0 ? (
                  <div className="error-message">
                    <strong>Debug:</strong> No measurements found in response.
                    <pre>{JSON.stringify(results.results.front, null, 2)}</pre>
                  </div>
                ) : (
                  <>
                    {/* Simple list view as fallback */}
                    <div style={{ marginBottom: '20px', padding: '15px', background: '#f9f9f9', borderRadius: '5px' }}>
                      <h5>Measurements List:</h5>
                      {Object.entries(results.results.front.measurements).map(([name, data]) => (
                        <div key={name} style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>
                          <strong>{name.replace(/_/g, ' ').toUpperCase()}:</strong>{' '}
                          {data.value_cm} cm ({data.value_px.toFixed(2)} px)
                        </div>
                      ))}
                    </div>

                    {/* Table view */}
                    <table>
                      <thead>
                        <tr>
                          <th>Measurement</th>
                          <th>Value (cm)</th>
                          <th>Value (px)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(results.results.front.measurements).map(([name, data]) => {
                          console.log(`📏 Rendering measurement: ${name}`, data);
                          return (
                            <tr key={name}>
                              <td>{name.replace(/_/g, ' ').toUpperCase()}</td>
                              <td>{data.value_cm} cm</td>
                              <td>{data.value_px.toFixed(2)} px</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Side View Results - Only for Automatic Mode */}
          {results.mode !== 'manual' && results.results.side && results.results.side.success && (
            <div className="view-results">
              <h3>Side View Measurements</h3>

              {/* Visualizations */}
              <div className="visualizations">
                <div className="vis-item">
                  <h4>Landmarks</h4>
                  <img src={results.results.side.visualization} alt="Side landmarks" />
                </div>
                <div className="vis-item">
                  <h4>Segmentation Mask</h4>
                  <img src={results.results.side.mask} alt="Side mask" />
                </div>
              </div>

              {/* Measurements Table */}
              <div className="measurements-table">
                <h4>Body Measurements</h4>
                <table>
                  <thead>
                    <tr>
                      <th>Measurement</th>
                      <th>Value (cm)</th>
                      <th>Value (px)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(results.results.side.measurements).map(([name, data]) => (
                      <tr key={name}>
                        <td>{name.replace(/_/g, ' ').toUpperCase()}</td>
                        <td>{data.value_cm} cm</td>
                        <td>{data.value_px} px</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="action-buttons">
            <button onClick={handleReset} className="reset-button">
              Process New Images
            </button>
            <button onClick={downloadJSON} className="download-button">
              Download JSON
            </button>
          </div>
        </div>
      )
      }

      {/* Mode Selection Modal */}
      {
        showModeSelection && (
          <ModeSelection
            onSelectMode={handleModeSelection}
            onCancel={() => setShowModeSelection(false)}
          />
        )
      }

      {/* Manual Landmark Marker */}
      {
        showManualMarker && (
          <ManualLandmarkMarker
            imageData={currentMarkingView === 'front' ? frontPreview : sidePreview}
            imageType={currentMarkingView}
            onComplete={handleManualLandmarkComplete}
            onCancel={handleManualMarkingCancel}
          />
        )
      }
    </div >
  );
};

export default UploadMode;
