import { useState, useEffect } from 'react';
import axios from 'axios';
import './UploadMode.css';
import ModeSelection from './ModeSelection';
import ManualLandmarkMarker from './ManualLandmarkMarker';
import SMPLViewer from './SMPLViewer';

const PoseSilhouette = () => (
  <div style={{ display: 'flex', gap: '2rem', justifyContent: 'center', margin: '1.5rem 0' }}>

    {/* Front View Silhouette */}
    <div style={{ textAlign: 'center' }}>
      <p style={{ fontWeight: 'bold', color: '#4caf50', marginBottom: '0.5rem' }}>✅ Front View</p>
      <svg width="160" height="320" viewBox="0 0 160 320" xmlns="http://www.w3.org/2000/svg">
        {/* Background */}
        <rect width="160" height="320" fill="#f0f8f0" rx="8"/>

        {/* Head */}
        <ellipse cx="80" cy="40" rx="22" ry="26" fill="#d4a574" stroke="#8B6914" strokeWidth="2"/>

        {/* Neck */}
        <rect x="72" y="63" width="16" height="15" fill="#d4a574"/>

        {/* Torso */}
        <path d="M52 78 L108 78 L112 175 L48 175 Z" fill="#4a90d9" stroke="#2c5f8a" strokeWidth="1.5"/>

        {/* Left Arm (slightly away from body) */}
        <path d="M52 85 L28 130 L22 175" stroke="#d4a574" strokeWidth="14" strokeLinecap="round" fill="none"/>

        {/* Right Arm (slightly away from body) */}
        <path d="M108 85 L132 130 L138 175" stroke="#d4a574" strokeWidth="14" strokeLinecap="round" fill="none"/>

        {/* Left Hand */}
        <ellipse cx="21" cy="180" rx="8" ry="10" fill="#d4a574"/>

        {/* Right Hand */}
        <ellipse cx="139" cy="180" rx="8" ry="10" fill="#d4a574"/>

        {/* Waist/Hip area */}
        <path d="M48 175 L50 210 L110 210 L112 175 Z" fill="#3a7bd5" stroke="#2c5f8a" strokeWidth="1.5"/>

        {/* Left Leg */}
        <path d="M60 210 L55 280 L68 280 L72 210 Z" fill="#2c3e6b" stroke="#1a2540" strokeWidth="1.5"/>

        {/* Right Leg */}
        <path d="M88 210 L92 280 L105 280 L100 210 Z" fill="#2c3e6b" stroke="#1a2540" strokeWidth="1.5"/>

        {/* Left Foot */}
        <ellipse cx="61" cy="284" rx="12" ry="6" fill="#8B6914"/>

        {/* Right Foot */}
        <ellipse cx="99" cy="284" rx="12" ry="6" fill="#8B6914"/>

        {/* Shoulder width measurement line */}
        <line x1="52" y1="78" x2="108" y2="78" stroke="#ff5722" strokeWidth="2" strokeDasharray="4,2"/>
        <line x1="52" y1="72" x2="52" y2="84" stroke="#ff5722" strokeWidth="2"/>
        <line x1="108" y1="72" x2="108" y2="84" stroke="#ff5722" strokeWidth="2"/>
        <text x="80" y="70" textAnchor="middle" fontSize="8" fill="#ff5722">shoulder</text>

        {/* Arm length measurement line */}
        <line x1="18" y1="85" x2="18" y2="175" stroke="#9c27b0" strokeWidth="2" strokeDasharray="4,2"/>
        <text x="10" y="135" fontSize="7" fill="#9c27b0" transform="rotate(-90,10,135)">arm</text>

        {/* Leg length measurement line */}
        <line x1="145" y1="210" x2="145" y2="280" stroke="#ff9800" strokeWidth="2" strokeDasharray="4,2"/>
        <line x1="140" y1="210" x2="150" y2="210" stroke="#ff9800" strokeWidth="2"/>
        <line x1="140" y1="280" x2="150" y2="280" stroke="#ff9800" strokeWidth="2"/>
        <text x="152" y="250" fontSize="7" fill="#ff9800" transform="rotate(90,152,250)">leg</text>

        {/* Torso measurement line */}
        <line x1="142" y1="78" x2="142" y2="175" stroke="#4caf50" strokeWidth="2" strokeDasharray="4,2"/>
        <line x1="137" y1="78" x2="147" y2="78" stroke="#4caf50" strokeWidth="2"/>
        <line x1="137" y1="175" x2="147" y2="175" stroke="#4caf50" strokeWidth="2"/>
        <text x="150" y="130" fontSize="7" fill="#4caf50" transform="rotate(90,150,130)">torso</text>

        {/* Green checkmark overlay */}
        <circle cx="140" cy="20" r="12" fill="#4caf50"/>
        <text x="140" y="25" textAnchor="middle" fontSize="14" fill="white">✓</text>
      </svg>
      <p style={{ fontSize: '12px', color: '#666', marginTop: '0.5rem' }}>Face camera directly</p>
    </div>

    {/* Side View Silhouette */}
    <div style={{ textAlign: 'center' }}>
      <p style={{ fontWeight: 'bold', color: '#4caf50', marginBottom: '0.5rem' }}>✅ Side View</p>
      <svg width="160" height="320" viewBox="0 0 160 320" xmlns="http://www.w3.org/2000/svg">
        {/* Background */}
        <rect width="160" height="320" fill="#f0f8f0" rx="8"/>

        {/* Head (side profile) */}
        <ellipse cx="85" cy="40" rx="20" ry="25" fill="#d4a574" stroke="#8B6914" strokeWidth="2"/>

        {/* Neck */}
        <rect x="78" y="63" width="12" height="14" fill="#d4a574"/>

        {/* Torso (side view - slightly curved) */}
        <path d="M65 77 L95 77 L98 175 L62 175 Z" fill="#4a90d9" stroke="#2c5f8a" strokeWidth="1.5"/>

        {/* Arm (side view - visible one arm) */}
        <path d="M65 85 L50 140 L46 178" stroke="#d4a574" strokeWidth="12" strokeLinecap="round" fill="none"/>
        <ellipse cx="45" cy="183" rx="7" ry="9" fill="#d4a574"/>

        {/* Hip/Waist */}
        <path d="M62 175 L63 212 L97 212 L98 175 Z" fill="#3a7bd5" stroke="#2c5f8a" strokeWidth="1.5"/>

        {/* Leg (side view) */}
        <path d="M72 212 L70 282 L82 282 L84 212 Z" fill="#2c3e6b" stroke="#1a2540" strokeWidth="1.5"/>

        {/* Foot */}
        <path d="M70 282 L95 282 L95 288 L70 288 Z" fill="#8B6914" rx="3"/>

        {/* Depth measurement line - chest */}
        <line x1="65" y1="110" x2="95" y2="110" stroke="#e91e63" strokeWidth="2" strokeDasharray="4,2"/>
        <text x="80" y="107" textAnchor="middle" fontSize="7" fill="#e91e63">chest depth</text>

        {/* Green checkmark */}
        <circle cx="140" cy="20" r="12" fill="#4caf50"/>
        <text x="140" y="25" textAnchor="middle" fontSize="14" fill="white">✓</text>
      </svg>
      <p style={{ fontSize: '12px', color: '#666', marginTop: '0.5rem' }}>Turn 90° to your right</p>
    </div>

    {/* Bad pose example */}
    <div style={{ textAlign: 'center' }}>
      <p style={{ fontWeight: 'bold', color: '#f44336', marginBottom: '0.5rem' }}>❌ Avoid This</p>
      <svg width="160" height="320" viewBox="0 0 160 320" xmlns="http://www.w3.org/2000/svg">
        {/* Background */}
        <rect width="160" height="320" fill="#fff0f0" rx="8"/>

        {/* Head */}
        <ellipse cx="80" cy="40" rx="22" ry="26" fill="#d4a574" stroke="#8B6914" strokeWidth="2"/>

        {/* Neck */}
        <rect x="72" y="63" width="16" height="15" fill="#d4a574"/>

        {/* Baggy torso */}
        <path d="M40 78 L120 78 L125 185 L35 185 Z" fill="#888" stroke="#555" strokeWidth="1.5"/>

        {/* Arms touching body */}
        <path d="M40 85 L35 160 L32 185" stroke="#d4a574" strokeWidth="14" strokeLinecap="round" fill="none"/>
        <path d="M120 85 L125 160 L128 185" stroke="#d4a574" strokeWidth="14" strokeLinecap="round" fill="none"/>

        {/* Baggy pants */}
        <path d="M35 185 L32 285 L55 285 L80 220 L105 285 L128 285 L125 185 Z" fill="#666" stroke="#444" strokeWidth="1.5"/>

        {/* X marks showing problems */}
        <text x="80" y="120" textAnchor="middle" fontSize="28" fill="#f44336" opacity="0.7">✗</text>

        {/* Labels */}
        <text x="80" y="300" textAnchor="middle" fontSize="8" fill="#f44336">Baggy clothes</text>
        <text x="80" y="310" textAnchor="middle" fontSize="8" fill="#f44336">Arms touching body</text>

        {/* Red X overlay */}
        <circle cx="140" cy="20" r="12" fill="#f44336"/>
        <text x="140" y="25" textAnchor="middle" fontSize="14" fill="white">✗</text>
      </svg>
      <p style={{ fontSize: '12px', color: '#f44336', marginTop: '0.5rem' }}>Baggy clothes + arms touching</p>
    </div>
  </div>
);

const PhotoGuidelines = ({ onProceed }) => (
  <div className="photo-guidelines">
    <h2>📸 Photo Guidelines for Accurate Measurements</h2>
    <p>Follow these instructions carefully before uploading your photos:</p>
    <PoseSilhouette />

    <div className="guidelines-grid">
      <div className="guideline-item good">
        <span className="icon">👕</span>
        <strong>Wear fitted clothing</strong>
        <p>Tight-fitting clothes (e.g. leggings, fitted t-shirt). Avoid loose, baggy, or layered clothing.</p>
      </div>
      <div className="guideline-item good">
        <span className="icon">📏</span>
        <strong>Stand 1.5–2 metres away</strong>
        <p>Your full body must be visible from head to toe with space around the edges.</p>
      </div>
      <div className="guideline-item good">
        <span className="icon">🧍</span>
        <strong>Stand straight, arms slightly out</strong>
        <p>Stand upright facing the camera. Keep arms slightly away from your body (A-pose).</p>
      </div>
      <div className="guideline-item good">
        <span className="icon">💡</span>
        <strong>Good lighting</strong>
        <p>Ensure the room is well-lit. Avoid strong backlighting or shadows on your body.</p>
      </div>
      <div className="guideline-item good">
        <span className="icon">📷</span>
        <strong>Camera at chest height</strong>
        <p>Place the camera at chest level, not from above or below.</p>
      </div>
      <div className="guideline-item good">
        <span className="icon">🧱</span>
        <strong>Plain background</strong>
        <p>Stand against a plain, single-colour wall for best segmentation accuracy.</p>
      </div>
      <div className="guideline-item bad">
        <span className="icon">❌</span>
        <strong>Avoid loose clothing</strong>
        <p>Baggy clothes hide your body shape and reduce measurement accuracy significantly.</p>
      </div>
      <div className="guideline-item bad">
        <span className="icon">❌</span>
        <strong>Avoid dark/busy backgrounds</strong>
        <p>Cluttered or dark backgrounds make it harder to detect your body outline.</p>
      </div>
    </div>

    <div className="guidelines-example">
      <div className="example good-example">
        <span>✅ Good pose</span>
        <p>Full body visible, arms slightly away, plain background, fitted clothes</p>
      </div>
      <div className="example bad-example">
        <span>❌ Bad pose</span>
        <p>Baggy clothes, arms touching body, cluttered background, partial body</p>
      </div>
    </div>

    <button className="proceed-btn" onClick={onProceed}>
      ✓ I Understand — Proceed to Upload
    </button>
  </div>
);

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

  // New states for image validation
  const [isValidatingFront, setIsValidatingFront] = useState(false);
  const [isValidatingSide, setIsValidatingSide] = useState(false);
  const [isFrontValidated, setIsFrontValidated] = useState(false);
  const [isSideValidated, setIsSideValidated] = useState(false);
  const [guidelinesAccepted, setGuidelinesAccepted] = useState(false);

  const validateImage = async (file, view, fileInput) => {
    if (view === 'front') {
      setIsValidatingFront(true);
      setIsFrontValidated(false);
    } else {
      setIsValidatingSide(true);
      setIsSideValidated(false);
    }
    setError(null);

    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('view', view);

      const response = await axios.post('/validate/person-count', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success) {
        if (view === 'front') {
          setIsFrontValidated(true);
        } else {
          setIsSideValidated(true);
        }
      } else {
        setError(response.data.error || `Validation failed for ${view} view.`);
        if (fileInput) fileInput.value = "";
        if (view === 'front') {
          setFrontImage(null);
          setFrontPreview(null);
        } else {
          setSideImage(null);
          setSidePreview(null);
        }
      }
    } catch (err) {
      console.error(`Validation error for ${view} view:`, err);
      const errMsg = err.response?.data?.error || `Validation failed for ${view} view. Please try again.`;
      setError(errMsg);
      if (fileInput) fileInput.value = "";
      if (view === 'front') {
        setFrontImage(null);
        setFrontPreview(null);
      } else {
        setSideImage(null);
        setSidePreview(null);
      }
    } finally {
      if (view === 'front') {
        setIsValidatingFront(false);
      } else {
        setIsValidatingSide(false);
      }
    }
  };

  const steps = [
    'Upload Photos',
    'Verify Identity', // Added verification step
    'Calculate Scale from Height',
    'YOLOv8 Segmentation',
    'MediaPipe Landmarks',
    'Compute Measurements',
    'Display Results'
  ];

  const formatPxValue = (value) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return '—';
    }
    return `${Number(value).toFixed(2)} px`;
  };

  const getSourceColor = (source) => {
    if (source === 'SMPL 3D Model') return '#2e7d32';
    if (source === 'SMPL + MediaPipe') return '#1565c0';
    if (source === 'Estimated') return '#b26a00';
    return '#2196f3';
  };

  const formatCmValue = (value) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return '—';
    }
    return `${Number(value).toFixed(1)} cm`;
  };

  const getSmplStatusBadge = (smpl) => {
    if (smpl?.fitted_to_user || smpl?.status === 'active') {
      return {
        className: 'smpl-fitted',
        text: '3D Body Model: Active',
      };
    }
    return {
      className: 'smpl-estimated',
      text: '3D Body Model: Estimated',
    };
  };

  // Effect to trigger verification when both images are present, or skip if only front is present
  useEffect(() => {
    if (frontImage && sideImage) {
      if (isFrontValidated && isSideValidated) {
        if (!isVerified && !isVerifying && !verificationError) {
          handleIdentityVerification();
        }
      } else {
        setIsVerified(false);
      }
    } else if (frontImage && !sideImage) {
      if (isFrontValidated) {
        setIsVerified(true);
        setVerificationError(null);
        setVerificationIssues({ front: [], side: [] });
      } else {
        setIsVerified(false);
      }
    } else {
      setIsVerified(false);
    }
  }, [frontImage, sideImage, isFrontValidated, isSideValidated]);

  const handleIdentityVerification = async () => {
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
        setVerificationError(null);
        setVerificationIssues({ front: [], side: [] });
      } else {
        const errorMsg = response.data.message || response.data.error || 'Face verification failed: Front and side photos belong to different people.';
        const issues = response.data.issues || { front: [], side: [] };
        console.error('✗ Verification failed:', errorMsg);
        setIsVerified(false);
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
      setIsVerified(false);
      setVerificationError(message);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleImageUpload = async (e, setImage, setPreview, view) => {
    if (e.target.files && e.target.files.length > 1) {
      setError("Please upload only one image at a time.");
      e.target.value = ""; // Clear input field
      return;
    }
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setIsVerified(false); // Reset verification if images change
      setVerificationError(null);
      setVerificationIssues({ front: [], side: [] }); // Clear issues on new upload
      setError(null); // Clear validation/person count errors on new upload
      setResults(null); // Clear previous results on new photo upload
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);

      // Reset validation states and clean other view values if front changes
      if (view === 'front') {
        setIsFrontValidated(false);
        setSideImage(null);
        setSidePreview(null);
        setIsSideValidated(false);
      } else {
        setIsSideValidated(false);
      }

      await validateImage(file, view, e.target);
    }
  };

  const resizeImage = (file, maxWidth = 1920, maxHeight = 1920) => {
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

  const handleResetLandmarks = () => {
    // Clear all manual landmarks but keep uploaded images
    setManualLandmarks({
      front: null,
      side: null
    });
    setResults(null);
    setError(null);
    // Restart manual marking from front view
    setCurrentMarkingView('front');
    setShowManualMarker(true);
    console.log('🔄 Landmarks reset - keeping uploaded images');
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
          timeout: 180000
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
          timeout: 180000
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
    setIsValidatingFront(false);
    setIsValidatingSide(false);
    setIsFrontValidated(false);
    setIsSideValidated(false);
    setGuidelinesAccepted(false);
  };

  const downloadReport = async (format) => {
    try {
      if (!results) {
        console.error("No results available for download");
        return;
      }

      const response = await axios.post(`/api/download/${format}`, {
        results: results?.results || {},
        calibration: results?.calibration || {},
        user_id: 'User_' + Math.floor(1000 + Math.random() * 9000) // Simple ID for now
      }, {
        responseType: 'blob', // Important for handling binary data
        timeout: 30000
      });

      // Create a blob from the response data
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Extract filename from content-disposition if available, else use a default
      const contentDisposition = response.headers ? response.headers['content-disposition'] : null;
      let filename = `FitLens_Report.${format}`;
      if (contentDisposition && contentDisposition.indexOf('filename=') !== -1) {
        filename = contentDisposition.split('filename=')[1].replace(/["']/g, '');
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      if (link.parentNode) {
        link.parentNode.removeChild(link);
      }
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(`❌ ${format.toUpperCase()} export error:`, err);
      alert(`Failed to download ${format.toUpperCase()} report. Please try again.`);
    }
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
        <>
          {!guidelinesAccepted && (
            <PhotoGuidelines onProceed={() => setGuidelinesAccepted(true)} />
          )}
          {guidelinesAccepted && (
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
                onChange={(e) => handleImageUpload(e, setFrontImage, setFrontPreview, 'front')}
                disabled={processing || isValidatingFront}
              />
              {isValidatingFront && (
                <div className="validation-spinner" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px', color: '#1890ff' }}>
                  <div className="spinner" style={{
                    width: '16px',
                    height: '16px',
                    border: '2px solid #f3f3f3',
                    borderTop: '2px solid #1890ff',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                  <span style={{ fontSize: '13px' }}>Validating photo...</span>
                </div>
              )}
              {frontPreview && !isValidatingFront && (
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
            {isFrontValidated && (
              <div className="upload-box">
                <h3>Side View (Optional)</h3>
                <p style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>
                  Side profile, full body visible
                </p>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleImageUpload(e, setSideImage, setSidePreview, 'side')}
                  disabled={processing || isValidatingSide}
                />
                {isValidatingSide && (
                  <div className="validation-spinner" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px', color: '#1890ff' }}>
                    <div className="spinner" style={{
                      width: '16px',
                      height: '16px',
                      border: '2px solid #f3f3f3',
                      borderTop: '2px solid #1890ff',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }}></div>
                    <span style={{ fontSize: '13px' }}>Validating photo...</span>
                  </div>
                )}
                {sidePreview && !isValidatingSide && (
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
            )}
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
            <div className="validation-error-box">
              <span className="error-icon">⚠️</span>
              <div className="error-content">
                <strong>Validation Error</strong>
                <p>{error}</p>
              </div>
            </div>
          )}

          {/* Process Button - Only show if verified */}
          {isVerified && (
            <button
              className="process-button"
              onClick={handleProcess}
              disabled={processing || !frontImage || !userHeight || error}
            >
              {processing ? 'Processing...' : 'Process Images'}
            </button>
          )}
            </div>
          )}
        </>
      ) : (
        <div className="results-section">
          <h2>
            Measurement Results
            {results?.mode && (
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
          {results?.mode === 'manual' && (
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

          {/* Automatic Mode Note */}
          {results?.mode !== 'manual' && (
            <div style={{
              background: '#e8f5e9',
              border: '1px solid #4caf50',
              padding: '12px',
              borderRadius: '5px',
              marginBottom: '20px'
            }}>
              <strong>ℹ️ Automatic Mode:</strong> AI-powered measurements using YOLOv8 segmentation + MediaPipe pose detection.
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
          {results?.calibration && (
            <div className="calibration-info">
              <h3>Height-Based Calibration</h3>
              <p><strong>Your Height:</strong> {results.calibration?.user_height_cm} cm</p>
              <p><strong>Height in Image:</strong> {results.calibration?.height_in_image_px?.toFixed(2)} pixels</p>
              <p><strong>Scale Factor:</strong> {results.calibration?.scale_factor?.toFixed(4)} cm/px</p>
              <p className="formula">{results.calibration?.formula}</p>
              <p style={{ fontSize: '14px', marginTop: '10px', fontStyle: 'italic' }}>
                {results.calibration?.description}
              </p>
            </div>
          )}

          {/* Debug Info */}
          {console.log('🔍 Rendering results:', {
            has_results: !!results,
            has_results_obj: !!results?.results,
            mode: results?.mode,
            has_merged: !!results?.results?.merged,
            has_front: !!results?.results?.front,
            front_success: results?.results?.front?.success,
            front_keys: results?.results?.front ? Object.keys(results.results.front) : [],
            has_measurements: !!results?.results?.front?.measurements,
            measurement_count: results?.results?.front?.measurements ? Object.keys(results.results.front.measurements).length : 0
          })}

          {/* CONSOLIDATED RESULTS VIEW */}
          {results?.results?.merged && (
            <div className="view-results">
              <h3>Final Measurements</h3>
              
              {results?.mode === 'manual' ? (
                <p style={{
                  color: '#ff9800',
                  fontSize: '14px',
                  fontStyle: 'italic',
                  marginBottom: '15px'
                }}>
                  ✋ Manual Mode: Consolidated measurements based on user-placed landmarks
                </p>
              ) : (
                <p style={{
                  color: '#4caf50',
                  fontSize: '14px',
                  fontStyle: 'italic',
                  marginBottom: '15px'
                }}>
                  🤖 Automatic Mode: Consolidated final measurements
                </p>
              )}

              {/* Visualizations - Show both Front and Side */}
              <div className="visualizations">
                {/* Front View */}
                {results?.results?.merged?.front_visualization && (
                  <div className="vis-item">
                    <h4>Front View - Marked Landmarks</h4>
                    <img src={results.results.merged.front_visualization} alt="Front view landmarks" />
                  </div>
                )}
                {results.results.merged.front_mask && (
                  <div className="vis-item">
                    <h4>Front View - Segmentation Mask</h4>
                    <img src={results.results.merged.front_mask} alt="Front mask" />
                  </div>
                )}

                {/* Side View */}
                {results?.results?.merged?.side_visualization && (
                  <div className="vis-item">
                    <h4>Side View - Marked Landmarks</h4>
                    <img src={results.results.merged.side_visualization} alt="Side view landmarks" />
                  </div>
                )}
                {results.results.merged.side_mask && (
                  <div className="vis-item">
                    <h4>Side View - Segmentation Mask</h4>
                    <img src={results.results.merged.side_mask} alt="Side mask" />
                  </div>
                )}

                {/* Fallback to legacy fields if new fields not available */}
                {!results?.results?.merged?.front_visualization && !results?.results?.merged?.side_visualization && results?.results?.merged?.visualization && (
                  <>
                    <div className="vis-item">
                      <h4>Marked Landmarks</h4>
                      <img src={results.results.merged.visualization} alt="Landmarks" />
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

              {/* 3D Body Model Viewer */}
              {(() => {
                const frontResult = results?.results?.front;
                const frontMeshData = frontResult?.mesh_data || results?.mesh_data;
                const apiSmplxStatus = frontResult?.smplx_status || results?.smplx_status;
                const showModelLoading = processing && (frontResult?.smpl?.status === 'active' || frontResult?.smpl?.status === 'estimated');
                const hasModel = !!(
                  frontMeshData?.x?.length &&
                  frontMeshData?.y?.length &&
                  frontMeshData?.z?.length &&
                  frontMeshData?.i?.length &&
                  frontMeshData?.j?.length &&
                  frontMeshData?.k?.length
                );
                const canShowPlaceholder = !hasModel && (frontResult?.smpl?.status === 'active' || frontResult?.smpl?.status === 'estimated' || !!frontResult?.smpl);
                const frontSmplStatus = getSmplStatusBadge(frontResult?.smpl);
                const smplStatusText = frontResult?.smpl?.status_text || 
                  (apiSmplxStatus === 'success' ? '✓ Model fitted to your body' : frontSmplStatus.text);

                if (!frontResult && !results?.mesh_data) return null;

                return (
                  <div style={{ marginTop: 24, marginBottom: 24 }}>
                    {showModelLoading ? (
                      <div style={{
                        height: 500,
                        background: '#1a1a2e',
                        borderRadius: 12,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#b0b6c5',
                        border: '1px solid #333'
                      }}>
                        <div className="spinner" />
                        <p style={{ marginTop: 12 }}>Building 3D body model...</p>
                        <p style={{ fontSize: 12, marginTop: 4 }}>Fitting SMPL model to your measurements</p>
                      </div>
                    ) : hasModel ? (
                      <SMPLViewer
                        meshData={frontMeshData}
                        statusText={smplStatusText}
                        statusDetail="Neutral pose · Interactive 3D viewer"
                      />
                    ) : canShowPlaceholder ? (
                      <div style={{
                        height: 500,
                        background: '#1a1a2e',
                        borderRadius: 12,
                        border: '1px solid #333',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#b0b6c5',
                        fontSize: 13
                      }}>
                        <div style={{ textAlign: 'center' }}>
                          <p>3D body model is not available for this result.</p>
                          <p style={{ fontSize: 11, color: '#666', marginTop: 4 }}>
                            (Status: {frontResult?.smpl?.status || 'N/A'}, Mesh: {hasModel ? 'Yes' : 'No'})
                          </p>
                        </div>
                      </div>
                    ) : null}
                  </div>
                );
              })()}

              {/* Hybrid Approach Info */}
              {results?.results?.front?.hybrid_approach && results.results.front.hybrid_approach.enabled && (
                <div style={{
                  background: '#e8f5e9',
                  border: '1px solid #4caf50',
                  padding: '12px',
                  borderRadius: '5px',
                  marginBottom: '20px'
                }}>
                  <strong>🔬 Hybrid Vision Approach:</strong>
                  <ul style={{ margin: '8px 0 0 20px', padding: 0 }}>
                    <li>Edge-based measurements (shoulder, chest, waist, hip widths): {results.results.front.hybrid_approach.source_summary?.segmentation_edge || 0}</li>
                    <li>MediaPipe joint measurements: {results.results.front.hybrid_approach.source_summary?.mediapipe_landmarks || 0}</li>
                  </ul>
                </div>
              )}

              {/* Consolidated Measurements Table */}
              <div className="measurements-table">
                <h4>Final Measurements ({results?.results?.merged?.measurements ? Object.keys(results.results.merged.measurements).length : 0} measurements)</h4>

                {!results?.results?.merged?.measurements || Object.keys(results.results.merged.measurements).length === 0 ? (
                  <div className="error-message">
                    <strong>No measurements found.</strong>
                  </div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Measurement</th>
                        <th>Value (cm)</th>
                        <th>Value (px)</th>
                        <th>Source</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(results.results.merged.measurements).map(([name, data]) => {
                        const sourceLabel = data.source || 'MediaPipe';
                        const sourceColor = getSourceColor(sourceLabel);
                        return (
                          <tr key={name}>
                            <td>{data.label || name.replace(/_/g, ' ').toUpperCase()}</td>
                            <td>{formatCmValue(data.value_cm)}</td>
                            <td>{formatPxValue(data.value_px)}</td>
                            <td style={{ color: sourceColor, fontSize: '12px', fontWeight: 'bold' }}>{sourceLabel}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>

              {/* Detailed Breakdown Collapsible */}
              {(results?.results?.front?.measurements || results?.results?.side?.measurements) && (
                <details style={{ marginTop: '30px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px', background: '#fafafa' }}>
                  <summary style={{ cursor: 'pointer', fontWeight: 'bold', fontSize: '16px', color: '#1890ff', outline: 'none' }}>
                    View detailed breakdown
                  </summary>
                  <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '30px' }}>
                    
                    {/* Front View Detailed Table */}
                    {results?.results?.front?.measurements && (
                      <div className="measurements-table">
                        <h4 style={{ color: '#4caf50' }}>Front View Measurements</h4>
                        <table>
                          <thead>
                            <tr>
                              <th>Measurement</th>
                              <th>Value (cm)</th>
                              <th>Value (px)</th>
                              <th>Source</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(results.results.front.measurements).map(([name, data]) => (
                              <tr key={name}>
                                <td>{data.label || name.replace(/_/g, ' ').toUpperCase()}</td>
                                <td>{formatCmValue(data.value_cm)}</td>
                                <td>{formatPxValue(data.value_px)}</td>
                                <td style={{ color: getSourceColor(data.source || 'MediaPipe'), fontSize: '12px' }}>
                                  {data.source || 'MediaPipe'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* Side View Detailed Table */}
                    {results?.results?.side?.measurements && (
                      <div className="measurements-table">
                        <h4 style={{ color: '#2196f3' }}>Side View Measurements</h4>
                        <table>
                          <thead>
                            <tr>
                              <th>Measurement</th>
                              <th>Value (cm)</th>
                              <th>Value (px)</th>
                              <th>Source</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(results.results.side.measurements).map(([name, data]) => (
                              <tr key={name}>
                                <td>{data.label || name.replace(/_/g, ' ').toUpperCase()}</td>
                                <td>{formatCmValue(data.value_cm)}</td>
                                <td>{formatPxValue(data.value_px)}</td>
                                <td style={{ color: getSourceColor(data.source || 'MediaPipe'), fontSize: '12px' }}>
                                  {data.source || 'MediaPipe'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                  </div>
                </details>
              )}

            </div>
          )}





          {/* Action Buttons */}
          <div className="action-buttons" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', justifyContent: 'center' }}>
            <button onClick={handleReset} className="reset-button">
              Process New Images
            </button>
            <button onClick={() => downloadReport('pdf')} className="download-button" style={{ backgroundColor: '#ff4d4f' }}>
              Download PDF
            </button>
            <button onClick={() => downloadReport('docx')} className="download-button" style={{ backgroundColor: '#1890ff' }}>
              Download DOCX
            </button>
            <button onClick={() => downloadReport('xml')} className="download-button" style={{ backgroundColor: '#52c41a' }}>
              Download XML
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
            onReset={handleResetLandmarks}
          />
        )
      }
    </div >
  );
};

export default UploadMode;
