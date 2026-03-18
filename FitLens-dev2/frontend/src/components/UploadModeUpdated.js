import React, { useState } from 'react';
import axios from 'axios';
import './UploadMode.css';

const UploadModeUpdated = () => {
  const [frontImage, setFrontImage] = useState(null);
  const [sideImage, setSideImage] = useState(null);
  const [referenceImage, setReferenceImage] = useState(null);
  
  const [frontPreview, setFrontPreview] = useState(null);
  const [sidePreview, setSidePreview] = useState(null);
  const [referencePreview, setReferencePreview] = useState(null);
  
  const [referenceWidth, setReferenceWidth] = useState('');
  const [referenceHeight, setReferenceHeight] = useState('');
  
  const [processing, setProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const steps = [
    'Upload Photos',
    'Detect Reference Object',
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
    
    if (!referenceImage) {
      setError('Please upload a reference image');
      return;
    }
    
    if (!referenceWidth || !referenceHeight) {
      setError('Please enter reference object dimensions');
      return;
    }

    setProcessing(true);
    setError(null);
    setResults(null);
    setCurrentStep(0);

    try {
      // Step 1: Upload Photos
      setCurrentStep(1);
      await new Promise(resolve => setTimeout(resolve, 500));

      const frontBase64 = await imageToBase64(frontImage);
      const sideBase64 = sideImage ? await imageToBase64(sideImage) : null;
      const referenceBase64 = await imageToBase64(referenceImage);

      // Send to backend
      const response = await axios.post('http://localhost:5000/api/process', {
        front_image: frontBase64,
        side_image: sideBase64,
        reference_image: referenceBase64,
        reference_width: parseFloat(referenceWidth),
        reference_height: parseFloat(referenceHeight)
      });

      // Simulate step progression (backend processes all steps)
      for (let step = 2; step <= 6; step++) {
        setCurrentStep(step);
        await new Promise(resolve => setTimeout(resolve, 800));
      }

      setResults(response.data);
      setProcessing(false);

    } catch (err) {
      console.error('Processing error:', err);
      setError(err.response?.data?.error || 'Processing failed. Please try again.');
      setProcessing(false);
      setCurrentStep(0);
    }
  };

  const handleReset = () => {
    setFrontImage(null);
    setSideImage(null);
    setReferenceImage(null);
    setFrontPreview(null);
    setSidePreview(null);
    setReferencePreview(null);
    setReferenceWidth('');
    setReferenceHeight('');
    setResults(null);
    setError(null);
    setCurrentStep(0);
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

            {/* Reference Image */}
            <div className="upload-box">
              <h3>Reference Object *</h3>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => handleImageUpload(e, setReferenceImage, setReferencePreview)}
                disabled={processing}
              />
              {referencePreview && (
                <div className="image-preview">
                  <img src={referencePreview} alt="Reference object" />
                </div>
              )}
            </div>
          </div>

          {/* Reference Dimensions */}
          <div className="reference-inputs">
            <h3>Reference Object Dimensions (cm)</h3>
            <div className="input-group">
              <label>
                Width (cm):
                <input
                  type="number"
                  step="0.1"
                  value={referenceWidth}
                  onChange={(e) => setReferenceWidth(e.target.value)}
                  placeholder="e.g., 8.5"
                  disabled={processing}
                />
              </label>
              <label>
                Height (cm):
                <input
                  type="number"
                  step="0.1"
                  value={referenceHeight}
                  onChange={(e) => setReferenceHeight(e.target.value)}
                  placeholder="e.g., 5.5"
                  disabled={processing}
                />
              </label>
            </div>
            <p className="hint">
              Example: Credit card is 8.5 cm × 5.5 cm
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
            disabled={processing || !frontImage || !referenceImage || !referenceWidth || !referenceHeight}
          >
            {processing ? 'Processing...' : 'Process Images'}
          </button>
        </div>
      ) : (
        <div className="results-section">
          <h2>Measurement Results</h2>
          
          {/* Calibration Info */}
          <div className="calibration-info">
            <h3>Reference Calibration</h3>
            <p>Reference: {results.reference_calibration.width_cm} cm × {results.reference_calibration.height_cm} cm</p>
            <p>Detected: {results.reference_calibration.width_px.toFixed(2)} px × {results.reference_calibration.height_px.toFixed(2)} px</p>
            <p>Scale Factor: {results.reference_calibration.scale_factor.toFixed(4)} cm/px</p>
            <p className="formula">{results.reference_calibration.formula}</p>
          </div>

          {/* Front View Results */}
          {results.results.front && results.results.front.success && (
            <div className="view-results">
              <h3>Front View Measurements</h3>
              
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
                <h4>Body Measurements</h4>
                <table>
                  <thead>
                    <tr>
                      <th>Measurement</th>
                      <th>Value (cm)</th>
                      <th>Value (px)</th>
                      <th>Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(results.results.front.measurements).map(([name, data]) => (
                      <tr key={name}>
                        <td>{name.replace(/_/g, ' ').toUpperCase()}</td>
                        <td>{data.value_cm} cm</td>
                        <td>{data.value_px} px</td>
                        <td>{(data.confidence * 100).toFixed(0)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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
                      <th>Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(results.results.side.measurements).map(([name, data]) => (
                      <tr key={name}>
                        <td>{name.replace(/_/g, ' ').toUpperCase()}</td>
                        <td>{data.value_cm} cm</td>
                        <td>{data.value_px} px</td>
                        <td>{(data.confidence * 100).toFixed(0)}%</td>
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
            <button 
              onClick={() => {
                const dataStr = JSON.stringify(results, null, 2);
                const dataBlob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'measurements.json';
                link.click();
              }}
              className="download-button"
            >
              Download JSON
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadModeUpdated;
