import React, { useState, useEffect, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import io from 'socket.io-client';
import axios from 'axios';
import ManualLandmarkMarker from './ManualLandmarkMarker';
import './LiveCamera.css';

// --- Silhouette Components ---
const SilhouetteSVG = ({ view, alignment, isAligned }) => {
    const viewLabel = view ? view.charAt(0).toUpperCase() + view.slice(1) : 'Front';
    const isGreen = isAligned || alignment === 'green';
    const silhouetteColor = isGreen ? '#00D4AA' : '#FF4444';
    const silhouetteFill = isGreen ? 'rgba(0,212,170,0.1)' : 'rgba(255,68,68,0.1)';

    if (viewLabel === 'Front' || viewLabel === 'Back') {
        return (
            <svg
                className="silhouette-svg"
                viewBox="0 0 200 480"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                style={{ width: '100%', height: '100%', opacity: 0.85 }}
            >
                <ellipse cx="100" cy="44" rx="28" ry="32" stroke={silhouetteColor} fill={silhouetteFill} strokeWidth="3" strokeDasharray="8,4"/>
                <rect x="88" y="74" width="24" height="22" rx="8" stroke={silhouetteColor} fill={silhouetteFill} strokeWidth="3" strokeDasharray="8,4"/>
                <path d="M44 110 Q60 90 88 96 L112 96 Q140 90 156 110" stroke={silhouetteColor} strokeWidth="3"/>
                <path d="M52 110 L44 210 Q60 228 100 230 Q140 228 156 210 L148 110" stroke={silhouetteColor} fill={silhouetteFill} strokeWidth="3"/>
                <path d="M56 210 Q100 240 144 210" stroke={silhouetteColor} strokeWidth="2" strokeDasharray="4,3"/>
                <path d="M44 210 Q36 250 40 270 L60 270 Q100 280 140 270 L160 270 Q164 250 156 210" stroke={silhouetteColor} strokeWidth="3"/>
                <path d="M52 110 L30 190 Q26 210 32 230 L48 230 L58 150" stroke={silhouetteColor} strokeWidth="3"/>
                <path d="M148 110 L170 190 Q174 210 168 230 L152 230 L142 150" stroke={silhouetteColor} strokeWidth="3"/>
                <path d="M60 270 L52 380 Q50 420 56 450 L80 450 L88 350 L92 270" stroke={silhouetteColor} fill={silhouetteFill} strokeWidth="3"/>
                <path d="M140 270 L148 380 Q150 420 144 450 L120 450 L112 350 L108 270" stroke={silhouetteColor} fill={silhouetteFill} strokeWidth="3"/>
                {viewLabel === 'Back' && <line x1="100" y1="96" x2="100" y2="270" stroke={silhouetteColor} strokeWidth="1" strokeDasharray="4,4" opacity="0.5"/>}
            </svg>
        );
    }

    const flipTransform = viewLabel === 'Left' ? 'scale(-1,1) translate(-200,0)' : '';

    return (
        <svg
            className="silhouette-svg"
            viewBox="0 0 200 480"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{ width: '100%', height: '100%', opacity: 0.85 }}
        >
            <g transform={flipTransform}>
                <ellipse cx="105" cy="44" rx="26" ry="32" stroke={silhouetteColor} fill={silhouetteFill} strokeWidth="3" strokeDasharray="8,4"/>
                <rect x="96" y="74" width="18" height="22" rx="6" stroke={silhouetteColor} fill={silhouetteFill} strokeWidth="3" strokeDasharray="8,4"/>
                <path d="M88 96 Q72 100 68 130 Q64 170 68 210 Q72 240 80 270" stroke={silhouetteColor} fill={silhouetteFill} strokeWidth="3"/>
                <path d="M106 96 Q120 104 122 130 Q126 170 118 210 Q112 240 108 270" stroke={silhouetteColor} strokeWidth="3"/>
                <path d="M68 130 L52 200 Q48 220 54 240 L68 238 L76 170" stroke={silhouetteColor} strokeWidth="3"/>
                <path d="M80 270 Q68 290 70 310 L100 315 Q118 308 108 270" stroke={silhouetteColor} strokeWidth="3"/>
                <path d="M72 310 L68 400 Q66 430 72 455 L90 455 L96 360 L100 315" stroke={silhouetteColor} fill={silhouetteFill} strokeWidth="3"/>
                <path d="M100 315 L104 400 Q108 430 102 455 L118 455 L116 360" stroke={silhouetteColor} fill={silhouetteFill} strokeWidth="3"/>
            </g>
        </svg>
    );
};

const SilhouetteOverlay = ({ view, alignment, isAligned }) => (
    <div className="silhouette-wrapper-overlay">
        <div className="corner-guide top-left" />
        <div className="corner-guide top-right" />
        <div className="corner-guide bottom-left" />
        <div className="corner-guide bottom-right" />
        <div className="silhouette-svg-inner">
            <SilhouetteSVG view={view} alignment={alignment} isAligned={isAligned} />
        </div>
    </div>
);

const LiveCamera = () => {
    const emptyLandmarksRef = useRef([]);
    const webcamRef = useRef(null);
    const [socket, setSocket] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [alignment, setAlignment] = useState('red');
    const [instruction, setInstruction] = useState('Connecting to camera...');
    const [cameraActive, setCameraActive] = useState(false);

    const [currentView, setCurrentView] = useState('front');
    const [captureStep, setCaptureStep] = useState('front'); // 'front' | 'side'
    const [capturedImages, setCapturedImages] = useState({});
    const [capturedRawImages, setCapturedRawImages] = useState({});

    // Fix 2: Distinct state variables for front and side view thumbnails
    const [frontCaptureUrl, setFrontCaptureUrl] = useState(null);
    const [sideCaptureUrl, setSideCaptureUrl] = useState(null);

    const [processing, setProcessing] = useState(false);
    const [results, setResults] = useState(null);
    const [isEditingMarkings, setIsEditingMarkings] = useState(false);
    const [userHeight, setUserHeight] = useState('');
    const [heightUnit, setHeightUnit] = useState('cm');
    const [sessionStarted, setSessionStarted] = useState(false);

    // Selection & workflow state
    const [awaitingSelection, setAwaitingSelection] = useState(false);
    const [lastCapturedImage, setLastCapturedImage] = useState(null);
    const [showManualMarker, setShowManualMarker] = useState(false);
    const [manualLandmarksByView, setManualLandmarksByView] = useState({});
    const [errorMsg, setErrorMsg] = useState(null);
    const [cameraStatus, setCameraStatus] = useState('initializing'); // 'initializing', 'ready', 'error'
    const [cameraErrorMsg, setCameraErrorMsg] = useState(null);
    const [countdown, setCountdown] = useState(3);
    const [isAligned, setIsAligned] = useState(false);
    const [facingMode, setFacingMode] = useState('user'); // 'user'=front, 'environment'=rear

    const flipCamera = useCallback(() => {
        setFacingMode(prev => (prev === 'user' ? 'environment' : 'user'));
        setIsAligned(false);
        isAlignedRef.current = false;
        if (countdownIntervalRef.current) {
            clearInterval(countdownIntervalRef.current);
            countdownIntervalRef.current = null;
        }
        countdownValueRef.current = 3;
        setCountdown(3);
    }, []);

    // Workflow state
    const VIEW_ORDER = ['front', 'side'];
    const [captureSequenceComplete, setCaptureSequenceComplete] = useState(false);
    const [markingMode, setMarkingMode] = useState(null); // 'manual' | 'auto'

    // Validation state
    const [validationError, setValidationError] = useState(null);
    const [isValidating, setIsValidating] = useState(false);
    const [markingViewIndex, setMarkingViewIndex] = useState(0);
    const [autoProgress, setAutoProgress] = useState({});
    const [autoViewOrder, setAutoViewOrder] = useState([]);
    const [isReviewing, setIsReviewing] = useState(false);
    const [completedViews, setCompletedViews] = useState([]);

    // Fix 1: Precise timer refs tracking alignment & countdown
    const countdownIntervalRef = useRef(null);
    const validationIntervalRef = useRef(null);
    const countdownValueRef = useRef(3);
    const isAlignedRef = useRef(false);
    const isCapturingRef = useRef(false);
    const currentViewRef = useRef(currentView);
    const markingViewIndexRef = useRef(0);
    const markingModeRef = useRef(null);
    const autoViewOrderRef = useRef([]);

    // Keep currentViewRef in sync with current state
    useEffect(() => {
        currentViewRef.current = currentView;
    }, [currentView]);

    useEffect(() => {
        markingViewIndexRef.current = markingViewIndex;
    }, [markingViewIndex]);

    useEffect(() => {
        markingModeRef.current = markingMode;
    }, [markingMode]);

    useEffect(() => {
        autoViewOrderRef.current = autoViewOrder;
    }, [autoViewOrder]);

    // Fix 3: Voice guidance control with immediate cancellation
    const stopVoiceGuidance = useCallback(() => {
        if (typeof window !== 'undefined' && window.speechSynthesis) {
            window.speechSynthesis.cancel(); // Stop immediately
        }
    }, []);

    const speakInstruction = useCallback((text) => {
        if (typeof window === 'undefined' || !window.speechSynthesis) return;
        window.speechSynthesis.cancel(); // Cancel current speech first
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        window.speechSynthesis.speak(utterance);
    }, []);

    // Fix 1: Clear all timers cleanly
    const clearAllTimers = useCallback(() => {
        if (countdownIntervalRef.current) {
            clearInterval(countdownIntervalRef.current);
            countdownIntervalRef.current = null;
        }
        if (validationIntervalRef.current) {
            clearInterval(validationIntervalRef.current);
            validationIntervalRef.current = null;
        }
        countdownValueRef.current = 3;
        isAlignedRef.current = false;
        setCountdown(3);
        setIsAligned(false);
    }, []);

    // Fix 2: Execute Capture with distinct state storage for front & side views
    const executeCapture = useCallback(async () => {
        stopVoiceGuidance(); // Stop speech immediately
        isCapturingRef.current = true;

        if (!webcamRef.current) return;
        const imageDataUrl = webcamRef.current.getScreenshot();
        if (!imageDataUrl) return;

        const activeView = currentViewRef.current || captureStep;

        if (activeView === 'front') {
            setFrontCaptureUrl(imageDataUrl); // Store front separately
            setCapturedImages(prev => ({ ...prev, front: imageDataUrl }));
            setCapturedRawImages(prev => ({ ...prev, front: imageDataUrl }));
            setCompletedViews(prev => [...new Set([...prev, 'front'])]);

            speakInstruction('Front view captured! Now turn 90 degrees to your right.');
            setTimeout(() => {
                isCapturingRef.current = false;
                switchToSideView(); // Switch to side view
            }, 2000);
        } else {
            setSideCaptureUrl(imageDataUrl); // Store side separately
            setCapturedImages(prev => ({ ...prev, side: imageDataUrl }));
            setCapturedRawImages(prev => ({ ...prev, side: imageDataUrl }));
            setCompletedViews(prev => [...new Set([...prev, 'side'])]);

            speakInstruction('Side view captured! Processing your measurements now.');
            setTimeout(() => {
                stopVoiceGuidance();
                isCapturingRef.current = false;
                setCameraActive(false);
                setIsReviewing(true);
            }, 1500);
        }
    }, [captureStep, speakInstruction, stopVoiceGuidance]);

    // Fix 1: Start 1-second ticks countdown using ref value
    const startCountdown = useCallback(() => {
        if (countdownIntervalRef.current) return; // Prevent duplicate timers

        countdownValueRef.current = 3;
        setCountdown(3);

        countdownIntervalRef.current = setInterval(() => {
            if (!isAlignedRef.current) {
                // Person misaligned — stop immediately
                clearInterval(countdownIntervalRef.current);
                countdownIntervalRef.current = null;
                countdownValueRef.current = 3;
                setCountdown(3);
                return;
            }

            countdownValueRef.current -= 1;
            setCountdown(countdownValueRef.current);

            if (countdownValueRef.current <= 0) {
                clearInterval(countdownIntervalRef.current);
                countdownIntervalRef.current = null;
                if (validationIntervalRef.current) {
                    clearInterval(validationIntervalRef.current);
                    validationIntervalRef.current = null;
                }
                executeCapture();
            }
        }, 1000); // Exactly 1 second — never faster
    }, [executeCapture]);

    // Fix 1: Switch from front to side view safely
    const switchToSideView = useCallback(() => {
        clearAllTimers();          // Clear everything first
        stopVoiceGuidance();       // Stop speech
        setCurrentView('side');
        setCaptureStep('side');
        setCountdown(3);
        setIsAligned(false);
    }, [clearAllTimers, stopVoiceGuidance]);

    // In-flight frame processing guard to prevent WebSocket buffer overflow
    const isProcessingFrameRef = useRef(false);
    const handlersAttachedRef = useRef(false);

    // Initialize Socket.io connection
    useEffect(() => {
        if (socketRef.current?.connected) return;

        const newSocket = io('http://localhost:5000', {
            transports: ['websocket', 'polling'],
            reconnectionAttempts: 3,
            reconnectionDelay: 2000,
        });
        socketRef.current = newSocket;

        if (!handlersAttachedRef.current) {
            handlersAttachedRef.current = true;

            newSocket.on('connect', () => {
                console.log('Connected to backend');
                setIsConnected(true);
                isProcessingFrameRef.current = false;
                setInstruction('Align yourself in the frame');
            });

            newSocket.on('disconnect', () => {
                console.log('Disconnected from backend');
                setIsConnected(false);
                isProcessingFrameRef.current = false;
                handlersAttachedRef.current = false;
                setInstruction('Connection lost. Reconnecting...');
            });

            newSocket.on('frame_processed', (data) => {
                isProcessingFrameRef.current = false; // Allow next frame to be sent
                setAlignment(data.alignment);
                setInstruction(data.instruction);

                const aligned = data.alignment === 'green';
                if (aligned && !isAlignedRef.current) {
                    isAlignedRef.current = true;
                    setIsAligned(true);
                    startCountdown();
                } else if (!aligned && isAlignedRef.current) {
                    isAlignedRef.current = false;
                    setIsAligned(false);
                    if (countdownIntervalRef.current) {
                        clearInterval(countdownIntervalRef.current);
                        countdownIntervalRef.current = null;
                        countdownValueRef.current = 3;
                        setCountdown(3);
                    }
                }

                if (data.speak) {
                    speakInstruction(data.instruction);
                }
            });

            newSocket.on('capture_complete', (data) => {
                console.log('Capture complete:', data);
                isProcessingFrameRef.current = false;
                if (data.view === 'front') {
                    setFrontCaptureUrl(data.image);
                } else if (data.view === 'side') {
                    setSideCaptureUrl(data.image);
                }
                setCapturedImages(prev => ({ ...prev, [data.view]: data.image }));
                setCompletedViews(prev => [...new Set([...prev, data.view])]);
                setAlignment('red');
                setIsAligned(false);
                isAlignedRef.current = false;

                if (data.voice_message) {
                    speakInstruction(data.voice_message);
                }

                if (data.next_view && data.next_view !== 'complete') {
                    switchToSideView();
                } else if (data.next_view === 'complete') {
                    stopVoiceGuidance();
                    setCameraActive(false);
                    setIsReviewing(true);
                }
            });

            newSocket.on('processing_complete', (data) => {
                console.log('Processing complete:', data);
                isProcessingFrameRef.current = false;
                setResults(data);
                setProcessing(false);
                setShowManualMarker(false);
                setIsEditingMarkings(false);
                speakInstruction('Processing complete. Your measurements are ready.');
            });

            newSocket.on('error', (err) => {
                console.error('Socket error:', err);
                isProcessingFrameRef.current = false;
                setInstruction(`Error: ${err.message}`);
            });
        }

        setSocket(newSocket);

        return () => {
            handlersAttachedRef.current = false;
            newSocket.disconnect();
        };
    }, [startCountdown, switchToSideView, speakInstruction, stopVoiceGuidance]);

    // Keep refs in sync for high-frequency frame loop
    const socketRef = useRef(socket);
    const userHeightRef = useRef(userHeight);
    const heightUnitRef = useRef(heightUnit);

    useEffect(() => {
        socketRef.current = socket;
    }, [socket]);

    useEffect(() => {
        userHeightRef.current = userHeight;
    }, [userHeight]);

    useEffect(() => {
        heightUnitRef.current = heightUnit;
    }, [heightUnit]);

    const captureAndSendFrame = useCallback(() => {
        if (webcamRef.current && socketRef.current && !isCapturingRef.current && !isProcessingFrameRef.current) {
            const imageSrc = webcamRef.current.getScreenshot();
            if (imageSrc) {
                isProcessingFrameRef.current = true; // Block sending next frame until backend responds
                socketRef.current.emit('process_frame', {
                    image: imageSrc,
                    view: currentViewRef.current,
                    user_height: parseFloat(userHeightRef.current),
                    height_unit: heightUnitRef.current
                });
            }
        }
    }, []);

    // Frame processing loop (5 FPS)
    useEffect(() => {
        if (!sessionStarted || !isConnected || !socket || !cameraActive || isReviewing) return;

        const interval = setInterval(() => {
            captureAndSendFrame();
        }, 200);

        return () => clearInterval(interval);
    }, [sessionStarted, isConnected, socket, cameraActive, isReviewing, captureAndSendFrame]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            stopVoiceGuidance();
            clearAllTimers();
            setCameraActive(false);
        };
    }, [clearAllTimers, stopVoiceGuidance]);

    const handleUserMedia = () => {
        setCameraStatus('ready');
    };

    const handleUserMediaError = (err) => {
        console.error('Webcam error:', err);
        setCameraStatus('error');
        setCameraErrorMsg('Failed to access camera. Please allow camera permissions.');
    };

    const startSession = () => {
        if (!userHeight) {
            alert('Please enter your height first');
            return;
        }
        stopVoiceGuidance();
        clearAllTimers();
        if (socket) {
            socket.emit('reset_session');
        }
        setCurrentView('front');
        setCaptureStep('front');
        setFrontCaptureUrl(null);
        setSideCaptureUrl(null);
        setCapturedImages({});
        setCapturedRawImages({});
        setCompletedViews([]);
        setSessionStarted(true);
        setCameraActive(true);
        setCameraStatus('initializing');
        setCameraErrorMsg(null);
        speakInstruction('Please face the front in A-pose.');
    };

    const resetSession = () => {
        stopVoiceGuidance(); // Stop voice guidance immediately
        clearAllTimers();    // Clear all timers
        setSessionStarted(false);
        setCameraActive(false);
        setFrontCaptureUrl(null);
        setSideCaptureUrl(null);
        setCapturedImages({});
        setCapturedRawImages({});
        setCompletedViews([]);
        setValidationError(null);
        setIsValidating(false);
        setLastCapturedImage(null);
        setAwaitingSelection(false);
        setShowManualMarker(false);
        setManualLandmarksByView({});
        setCurrentView('front');
        setCaptureStep('front');
        setResults(null);
        setProcessing(false);
        setErrorMsg(null);
        setIsReviewing(false);
        setInstruction('Align yourself in the frame');
        setAlignment('red');
        setCameraStatus('initializing');
        setCameraErrorMsg(null);
        setCaptureSequenceComplete(false);
        setMarkingMode(null);
        setMarkingViewIndex(0);
        setAutoProgress({});
        setAutoViewOrder([]);
        autoViewOrderRef.current = [];
        setIsEditingMarkings(false);
        if (socket) {
            socket.emit('reset_session');
        }
    };

    const handleManualCapture = () => {
        executeCapture();
    };

    const handleRetakeView = (view) => {
        stopVoiceGuidance();
        clearAllTimers();
        setCurrentView(view);
        setCaptureStep(view);
        if (view === 'front') {
            setFrontCaptureUrl(null);
        } else {
            setSideCaptureUrl(null);
        }
        setIsReviewing(false);
        setCameraActive(true);
        setCompletedViews(prev => prev.filter(v => v !== view));
        setManualLandmarksByView(prev => {
            const next = { ...prev };
            delete next[view];
            return next;
        });
        setCaptureSequenceComplete(false);
        setAwaitingSelection(false);
        setMarkingMode(null);
    };

    const handleAutomaticMarking = () => {
        stopVoiceGuidance();
        const capturedOrder = VIEW_ORDER.filter(view => Boolean(capturedImages[view] || (view === 'front' ? frontCaptureUrl : sideCaptureUrl)));
        if (capturedOrder.length === 0) {
            alert('No captured photos found. Please capture photos first.');
            return;
        }

        setAwaitingSelection(false);
        setMarkingMode('auto');
        setMarkingViewIndex(0);
        setAutoViewOrder(capturedOrder);
        autoViewOrderRef.current = capturedOrder;
        setAutoProgress({});
        markingModeRef.current = 'auto';
        markingViewIndexRef.current = 0;
        processNextAutoView(0, capturedOrder);
    };

    const processNextAutoView = (index, explicitOrder = null) => {
        const orderedViews = explicitOrder || autoViewOrderRef.current;
        if (!orderedViews || index >= orderedViews.length) {
            setProcessing(true);
            setInstruction('Finalizing analysis...');
            if (socket && socket.connected) {
                socket.emit('finalize_session');
            }
            
            // Backup REST call to guarantee completion even if WebSocket drops or disconnects
            setTimeout(async () => {
                try {
                    console.log('Sending fallback REST finalize-session request...');
                    const resp = await axios.post('/api/finalize-session', {
                        front_image: frontCaptureUrl || capturedImages['front'],
                        side_image: sideCaptureUrl || capturedImages['side'],
                        user_height: parseFloat(userHeight),
                        height_unit: heightUnit
                    });
                    if (resp.data && resp.data.results) {
                        setResults(resp.data);
                        setProcessing(false);
                    }
                } catch (err) {
                    console.log('REST finalize fallback status:', err);
                }
            }, 3500);
            return;
        }

        const view = orderedViews[index];
        const imgUrl = capturedImages[view] || (view === 'front' ? frontCaptureUrl : sideCaptureUrl);
        setProcessing(true);
        setInstruction(`Processing photo ${index + 1} of ${orderedViews.length}...`);
        setAutoProgress(prev => ({ ...prev, [view]: 'processing' }));
        
        socket.emit('process_selection', {
            view: view,
            image: imgUrl,
            type: 'auto',
            user_height: parseFloat(userHeight),
            height_unit: heightUnit
        });
    };

    const handleManualMarking = () => {
        stopVoiceGuidance();
        setAwaitingSelection(false);
        setIsEditingMarkings(false);
        setMarkingMode('manual');
        setMarkingViewIndex(0);
        markingModeRef.current = 'manual';
        markingViewIndexRef.current = 0;
        setShowManualMarker(true);
    };

    // Fix 4: Dynamic silhouette color & status text styling
    const isAlignedState = isAligned || alignment === 'green';
    const silhouetteColor = isAlignedState ? '#00D4AA' : '#FF4444';

    if (results) {
        return (
            <div className="results-container">
                <h2>Analysis Complete</h2>
                <pre>{JSON.stringify(results, null, 2)}</pre>
                <button onClick={resetSession} className="start-button">Start New Session</button>
            </div>
        );
    }

    if (showManualMarker) {
        return (
            <ManualLandmarkMarker
                imageData={frontCaptureUrl || capturedImages['front']}
                frontImage={frontCaptureUrl || capturedImages['front']}
                sideImage={sideCaptureUrl || capturedImages['side']}
                imageType="front"
                views={VIEW_ORDER.filter(v => Boolean(capturedImages[v] || (v === 'front' ? frontCaptureUrl : sideCaptureUrl)))}
                capturedImages={capturedImages}
                userHeight={userHeight}
                heightUnit={heightUnit}
                onComplete={() => {
                    setShowManualMarker(false);
                    setIsReviewing(true);
                }}
                onCancel={() => {
                    setShowManualMarker(false);
                    setIsReviewing(true);
                }}
            />
        );
    }

    if (isReviewing) {
        return (
            <div className="camera-review-screen">
                <h2>All photos captured</h2>
                <div className="review-grid-row">
                    {/* Fix 2: Render thumbnails correctly using distinct variables */}
                    <div className="review-thumb">
                        <div className="thumb-wrapper">
                            <img src={frontCaptureUrl || capturedImages['front']} alt="Front view" />
                        </div>
                        <span className="thumb-label">✓ Front View</span>
                        <button onClick={() => handleRetakeView('front')} className="mini-retake-btn">
                            Retake
                        </button>
                    </div>

                    <div className="review-thumb">
                        <div className="thumb-wrapper">
                            <img src={sideCaptureUrl || capturedImages['side']} alt="Side view" />
                        </div>
                        <span className="thumb-label">✓ Side View</span>
                        <button onClick={() => handleRetakeView('side')} className="mini-retake-btn">
                            Retake
                        </button>
                    </div>
                </div>
                
                <div className="review-footer">
                    <p className="reference-height">Height: <strong>{userHeight} {heightUnit}</strong></p>
                    <h3>Choose how to detect measurements</h3>
                    <div className="selection-buttons">
                        <button onClick={handleManualMarking} className="method-button manual">
                            <strong>Manual Marking</strong>
                            <span>User places points manually on body</span>
                        </button>
                        <button onClick={handleAutomaticMarking} className="method-button automatic" disabled={processing}>
                            {processing ? 'Processing...' : (
                                <>
                                    <strong>Automatic Marking</strong>
                                    <span>AI detects points automatically</span>
                                </>
                            )}
                        </button>
                    </div>
                    <button onClick={resetSession} className="cancel-btn-large">Cancel</button>
                </div>
            </div>
        );
    }

    return (
        <div className="live-camera-container">
            {!sessionStarted ? (
                <div className="setup-screen">
                    <h2>Live Camera Mode</h2>
                    <p style={{ marginBottom: '20px', color: 'black' }}>
                        Stand at approximately 1 meter from the camera with your full body visible
                    </p>
                    <div className="input-group">
                        <label>
                            Enter Your Height:
                            <input
                                type="number"
                                value={userHeight}
                                onChange={(e) => setUserHeight(e.target.value)}
                                placeholder="e.g. 170"
                            />
                        </label>
                        <select value={heightUnit} onChange={(e) => setHeightUnit(e.target.value)}>
                            <option value="cm">cm</option>
                            <option value="inches">inches</option>
                            <option value="feet">feet</option>
                        </select>
                    </div>
                    <button onClick={startSession} className="start-button">Start Camera</button>
                </div>
            ) : (
                <div className={`camera-view ${isAlignedState ? 'green' : 'red'}`}>
                    <div className="camera-header-tabs">
                        {VIEW_ORDER.map((view) => {
                            const isDone = completedViews.includes(view) || (view === 'front' ? !!frontCaptureUrl : !!sideCaptureUrl);
                            return (
                                <div key={view} className={`tab-item ${currentView === view ? 'active' : ''} ${isDone ? 'completed' : ''}`}>
                                    {isDone && <span className="check">✓</span>}
                                    {view.toUpperCase()}
                                </div>
                            );
                        })}
                    </div>

                    <div className="view-instruction-overlay">
                        <h2>{VIEW_ORDER.indexOf(currentView) + 1} of {VIEW_ORDER.length} — {currentView.charAt(0).toUpperCase() + currentView.slice(1)} View</h2>
                        
                        {/* Fix 4: Alignment status text with dynamic color */}
                        <div className="alignment-status" style={{ color: silhouetteColor, fontWeight: 'bold', fontSize: '16px', marginTop: '6px' }}>
                            {isAlignedState
                                ? `✅ Aligned! Capturing in ${countdown}...`
                                : captureStep === 'front' || currentView === 'front'
                                ? '👤 Stand facing camera in A-pose'
                                : '↩️ Turn 90° to your right for side view'}
                        </div>
                    </div>

                    <div className="webcam-wrapper">
                        {cameraStatus === 'initializing' && (
                            <div className="camera-loading">
                                <div className="spinner-large"></div>
                                <p>Starting camera...</p>
                            </div>
                        )}

                        {cameraStatus === 'error' && (
                            <div className="camera-error">
                                <div className="error-icon">⚠️</div>
                                <p>{cameraErrorMsg}</p>
                                <button onClick={resetSession} className="retry-button">Try Again</button>
                            </div>
                        )}

                        {isValidating && (
                            <div className="camera-loading" style={{ background: 'rgba(0,0,0,0.75)', color: 'white', zIndex: 30 }}>
                                <div className="spinner-large" style={{ borderTopColor: '#00FF88' }}></div>
                                <p>Validating photo...</p>
                            </div>
                        )}

                        {validationError && (
                            <div className="validation-error-overlay">
                                <div className="validation-error-content">
                                    <div className="error-icon">⚠️</div>
                                    <p className="error-msg-text">{validationError}</p>
                                    <button 
                                        onClick={() => { 
                                            setValidationError(null); 
                                            setCameraActive(true); 
                                        }} 
                                        className="validation-retry-btn"
                                    >
                                        Retake Photo
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Fix 4: Silhouette color dynamic stroke/fill */}
                        <SilhouetteOverlay view={currentView} alignment={alignment} isAligned={isAlignedState} />

                        {/* Auto-capture countdown overlay */}
                        {isAlignedState && (
                            <div className="auto-capture-overlay">
                                <div className="countdown-ring">
                                    <svg viewBox="0 0 100 100">
                                        <circle cx="50" cy="50" r="42" className="countdown-bg" />
                                        <circle
                                            cx="50" cy="50" r="42"
                                            className="countdown-progress"
                                            strokeDasharray={`${((countdown / 3) * 263.9).toFixed(1)} 263.9`}
                                        />
                                    </svg>
                                    <span className="countdown-number">{countdown}</span>
                                </div>
                                <p className="auto-capture-hint">Hold still…</p>
                            </div>
                        )}

                        {/* Misaligned hint */}
                        {!isAlignedState && cameraActive && (
                            <div className="alignment-hint-text">Align yourself in the frame</div>
                        )}

                        {/* Camera flip button */}
                        {cameraActive && (
                            <button
                                onClick={flipCamera}
                                style={{
                                    position: 'absolute',
                                    top: 16, right: 16,
                                    background: 'rgba(0,0,0,0.6)',
                                    border: '2px solid #00d4aa',
                                    borderRadius: '50%',
                                    width: 48, height: 48,
                                    color: '#00d4aa', fontSize: 22,
                                    cursor: 'pointer', zIndex: 20,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                }}
                                title={facingMode === 'user' ? 'Switch to Rear Camera' : 'Switch to Front Camera'}>
                                🔄
                            </button>
                        )}

                        {/* Camera mode badge */}
                        {cameraActive && (
                            <div style={{
                                position: 'absolute', top: 16, left: 16,
                                background: 'rgba(0,0,0,0.6)',
                                color: '#00d4aa', padding: '4px 10px',
                                borderRadius: 20, fontSize: 12, fontWeight: 700, zIndex: 20
                            }}>
                                {facingMode === 'user' ? '📷 Front Camera' : '📷 Rear Camera'}
                            </div>
                        )}

                        {cameraActive && (
                            <Webcam
                                ref={webcamRef}
                                audio={false}
                                screenshotFormat="image/jpeg"
                                width={640}
                                height={480}
                                onUserMedia={handleUserMedia}
                                onUserMediaError={handleUserMediaError}
                                videoConstraints={{
                                    facingMode: facingMode,
                                    width: { ideal: 1280 },
                                    height: { ideal: 720 }
                                }}
                                style={{
                                    visibility: cameraStatus === 'ready' ? 'visible' : 'hidden'
                                }}
                            />
                        )}
                    </div>

                    <div className="camera-controls">
                        {(() => {
                            const isCaptureDisabled = instruction && instruction.includes("Multiple people detected");
                            return (
                                <button 
                                    onClick={handleManualCapture} 
                                    className="capture-btn-main"
                                    disabled={isCaptureDisabled || isValidating || !!validationError}
                                >
                                    <div className="capture-inner"></div>
                                </button>
                            );
                        })()}
                        <button onClick={resetSession} className="cancel-text-btn">Cancel</button>
                    </div>

                    {/* Fix 2: Render thumbnails at bottom of camera view */}
                    <div className="capture-thumbnails-strip" style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                        {frontCaptureUrl && (
                            <div className="capture-thumbnail front-thumbnail" style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(0,0,0,0.6)', padding: '4px 8px', borderRadius: '6px', color: '#00FF88', fontSize: '12px' }}>
                                <img src={frontCaptureUrl} alt="Front view" style={{ width: '32px', height: '32px', borderRadius: '4px', objectFit: 'cover' }} />
                                <span>✓ Front View</span>
                            </div>
                        )}
                        {sideCaptureUrl && (
                            <div className="capture-thumbnail side-thumbnail" style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(0,0,0,0.6)', padding: '4px 8px', borderRadius: '6px', color: '#00FF88', fontSize: '12px' }}>
                                <img src={sideCaptureUrl} alt="Side view" style={{ width: '32px', height: '32px', borderRadius: '4px', objectFit: 'cover' }} />
                                <span>✓ Side View</span>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default LiveCamera;
