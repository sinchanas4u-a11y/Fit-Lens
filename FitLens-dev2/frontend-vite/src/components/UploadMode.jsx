import { useState } from 'react';
import axios from 'axios';
import './UploadMode.css';

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

  const steps = [
    'Upload Photos',
    'Calculate Scale from Height',
    'YOLOv8 Segmentation',
    'MediaPipe Landmarks',
    'Compute Measurements',
    'Display Results'
  ];

  const handleImageUpload = (e, setImage, setPreview) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const imageToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleProcess = async () => {
    // Validation
    if (!frontImage) {
      setError('Please upload a front view image');
      return;
    }

    if (!userHeight) {
      setError('Please enter your height');
      return;
    }

    setProcessing(true);
    setError(null);
    setResults(null);
    setCurrentStep(0);

    try {
      console.log('🚀 Starting image processing...');

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
      const response = await axios.post('/api/process', requestData);

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
      for (let step = 2; step <= 6; step++) {
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
      setError(err.response?.data?.error || 'Processing failed. Please try again.');
      setProcessing(false);
      setCurrentStep(0);
    }
  };

  const handleReset = () => {
    setFrontImage(null);
    setSideImage(null);
    setFrontPreview(null);
    setSidePreview(null);
    setUserHeight('');
    setResults(null);
    setError(null);
    setCurrentStep(0);
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
            </div>
          </div>

          {/* User Height Input */}
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

          {/* Error Message */}
          {error && (
            <div className="error-message">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Process Button */}
          <button
            className="process-button"
            onClick={handleProcess}
            disabled={processing || !frontImage || !userHeight}
          >
            {processing ? 'Processing...' : 'Process Images'}
          </button>
        </div>
      ) : (
        <div className="results-section">
          <h2>Measurement Results</h2>

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
            has_front: !!results?.results?.front,
            front_success: results?.results?.front?.success,
            has_measurements: !!results?.results?.front?.measurements,
            measurement_count: results?.results?.front?.measurements ? Object.keys(results.results.front.measurements).length : 0
          })}

          {/* Front View Results */}
          {results.results.front && results.results.front.success && (
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

          {/* Side View Results */}
          {results.results.side && results.results.side.success && (
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
      )}
    </div>
  );
};

export default UploadMode;
