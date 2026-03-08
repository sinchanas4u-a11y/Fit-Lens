import React, { useState, useEffect, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import io from 'socket.io-client';
import ManualLandmarkMarker from './ManualLandmarkMarker';
import './LiveCamera.css';

// --- Silhouette Components ---
const SilhouetteSVG = ({ view }) => {
    const viewLabel = view ? view.charAt(0).toUpperCase() + view.slice(1) : 'Front';

    if (viewLabel === 'Front' || viewLabel === 'Back') {
        return (
            <svg
                viewBox="0 0 200 480"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                style={{ width: '100%', height: '100%', opacity: 0.35 }}
            >
                <ellipse cx="100" cy="44" rx="28" ry="32" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <rect x="88" y="74" width="24" height="22" rx="8" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M44 110 Q60 90 88 96 L112 96 Q140 90 156 110" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M52 110 L44 210 Q60 228 100 230 Q140 228 156 210 L148 110" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M56 210 Q100 240 144 210" stroke="#00FF88" strokeWidth="2" strokeDasharray="4 3"/>
                <path d="M44 210 Q36 250 40 270 L60 270 Q100 280 140 270 L160 270 Q164 250 156 210" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M52 110 L30 190 Q26 210 32 230 L48 230 L58 150" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M148 110 L170 190 Q174 210 168 230 L152 230 L142 150" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M60 270 L52 380 Q50 420 56 450 L80 450 L88 350 L92 270" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M140 270 L148 380 Q150 420 144 450 L120 450 L112 350 L108 270" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                {viewLabel === 'Back' && <line x1="100" y1="96" x2="100" y2="270" stroke="#00FF88" strokeWidth="1" strokeDasharray="4 4" opacity="0.5"/>}
            </svg>
        );
    }

    const flipTransform = viewLabel === 'Left' ? 'scale(-1,1) translate(-200,0)' : '';

    return (
        <svg
            viewBox="0 0 200 480"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{ width: '100%', height: '100%', opacity: 0.35 }}
        >
            <g transform={flipTransform}>
                <ellipse cx="105" cy="44" rx="26" ry="32" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <rect x="96" y="74" width="18" height="22" rx="6" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M88 96 Q72 100 68 130 Q64 170 68 210 Q72 240 80 270" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M106 96 Q120 104 122 130 Q126 170 118 210 Q112 240 108 270" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M68 130 L52 200 Q48 220 54 240 L68 238 L76 170" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M80 270 Q68 290 70 310 L100 315 Q118 308 108 270" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M72 310 L68 400 Q66 430 72 455 L90 455 L96 360 L100 315" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
                <path d="M100 315 L104 400 Q108 430 102 455 L118 455 L116 360" stroke="#00FF88" strokeWidth="2.5" strokeDasharray="6 3"/>
            </g>
        </svg>
    );
};

const SilhouetteOverlay = ({ view }) => (
    <div className="silhouette-wrapper-overlay">
        <div className="corner-guide top-left" />
        <div className="corner-guide top-right" />
        <div className="corner-guide bottom-left" />
        <div className="corner-guide bottom-right" />
        <div className="silhouette-svg-inner">
            <SilhouetteSVG view={view} />
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
    
    // Lifecycle management
    useEffect(() => {
        // Stop camera on unmount
        return () => {
            setCameraActive(false);
        };
    }, []);
    
    const [currentView, setCurrentView] = useState('front');
    const [capturedImages, setCapturedImages] = useState({});
    const [capturedRawImages, setCapturedRawImages] = useState({});
    const [processing, setProcessing] = useState(false);
    const [results, setResults] = useState(null);
    const [isEditingMarkings, setIsEditingMarkings] = useState(false);
    const [userHeight, setUserHeight] = useState('');
    const [heightUnit, setHeightUnit] = useState('cm');
    const [sessionStarted, setSessionStarted] = useState(false);
    
    // Selection state
    const [awaitingSelection, setAwaitingSelection] = useState(false);
    const [lastCapturedImage, setLastCapturedImage] = useState(null);
    const [showManualMarker, setShowManualMarker] = useState(false);
    const [manualLandmarksByView, setManualLandmarksByView] = useState({});
    const [errorMsg, setErrorMsg] = useState(null);
    const [cameraStatus, setCameraStatus] = useState('initializing'); // 'initializing', 'ready', 'error'
    const [cameraErrorMsg, setCameraErrorMsg] = useState(null);
    const [countdown, setCountdown] = useState(null);
    
    // Workflow state
    const VIEW_ORDER = ['front', 'right', 'back', 'left'];
    const [captureSequenceComplete, setCaptureSequenceComplete] = useState(false);
    const [markingMode, setMarkingMode] = useState(null); // 'manual' | 'auto'
    const [markingViewIndex, setMarkingViewIndex] = useState(0);
    const [autoProgress, setAutoProgress] = useState({}); // {front: 'done', right: 'processing', ...}
    const [isReviewing, setIsReviewing] = useState(false);
    const [completedViews, setCompletedViews] = useState([]);

    // Auto-capture state
    const [captureCountdown, setCaptureCountdown] = useState(null); // 3, 2, 1, 0
    const captureTimerRef = useRef(null);
    const currentViewRef = useRef(currentView);
    const markingViewIndexRef = useRef(0);
    const markingModeRef = useRef(null);

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

    // Auto-capture: start/stop countdown based on alignment
    useEffect(() => {
        if (!sessionStarted || !cameraActive || isReviewing) {
            clearInterval(captureTimerRef.current);
            setCaptureCountdown(null);
            return;
        }

        if (alignment === 'green') {
            // Start a 3-second countdown if not already running
            if (captureTimerRef.current === null) {
                setCaptureCountdown(3);
                let count = 3;
                captureTimerRef.current = setInterval(() => {
                    count -= 1;
                    setCaptureCountdown(count);
                    if (count <= 0) {
                        clearInterval(captureTimerRef.current);
                        captureTimerRef.current = null;
                        setCaptureCountdown(null);
                        // Trigger auto-capture
                        triggerAutoCapture();
                    }
                }, 1000);
            }
        } else {
            // User moved out of frame — reset
            clearInterval(captureTimerRef.current);
            captureTimerRef.current = null;
            setCaptureCountdown(null);
        }

        return () => {
            clearInterval(captureTimerRef.current);
            captureTimerRef.current = null;
        };
    }, [alignment, sessionStarted, cameraActive, isReviewing]);

    // Initialize Socket.io
    useEffect(() => {
        const newSocket = io('http://localhost:5001');

        newSocket.on('connect', () => {
            console.log('Connected to backend');
            setIsConnected(true);
            setInstruction('Align yourself in the frame');
        });

        newSocket.on('disconnect', () => {
            console.log('Disconnected from backend');
            setIsConnected(false);
            setInstruction('Connection lost. Reconnecting...');
        });

        newSocket.on('frame_processed', (data) => {
            setAlignment(data.alignment);
            setInstruction(data.instruction);
            setCountdown(data.countdown);

            if (data.speak) {
                speak(data.instruction);
            }
        });

        newSocket.on('capture_complete', (data) => {
            console.log('Capture complete:', data);
            setCapturedImages(prev => ({ ...prev, [data.view]: data.image }));
            setCompletedViews(prev => [...new Set([...prev, data.view])]);
            
            // In the new flow, we handle view switching manually or via capture button
            // but the socket still confirms "captured"
        });

        newSocket.on('processing_complete', (data) => {
            console.log('Processing complete:', data);
            setResults(data);
            setProcessing(false);
            setShowManualMarker(false);
            setIsEditingMarkings(false);
            speak('Processing complete. Your measurements are ready.');
        });

        newSocket.on('error', (err) => {
            console.error('Socket error:', err);
            setInstruction(`Error: ${err.message}`);
        });

        setSocket(newSocket);

        return () => newSocket.close();
    }, []);

    // Frame processing loop
    useEffect(() => {
        if (!sessionStarted || !isConnected || !socket || !cameraActive || isReviewing) return;

        const interval = setInterval(() => {
            captureAndSendFrame();
        }, 200); // 5 FPS

        return () => clearInterval(interval);
    }, [sessionStarted, isConnected, socket, currentView, userHeight, heightUnit, cameraActive, isReviewing]);

    const captureAndSendFrame = useCallback(() => {
        if (webcamRef.current) {
            const imageSrc = webcamRef.current.getScreenshot();
            if (imageSrc) {
                socket.emit('process_frame', {
                    image: imageSrc,
                    view: currentView,
                    user_height: parseFloat(userHeight),
                    height_unit: heightUnit
                });
            }
        }
    }, [socket, currentView, userHeight, heightUnit]);

    const speak = (text) => {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
        }
    };

    const startSession = () => {
        if (!userHeight) {
            alert('Please enter your height first');
            return;
        }
        setSessionStarted(true);
        setCameraActive(true);
        setCameraStatus('initializing');
        setCameraErrorMsg(null);
        speak('Please face the front.');
    };

    const resetSession = () => {
        setSessionStarted(false);
        setCameraActive(false);
        setCapturedImages({});
        setCapturedRawImages({});
        setCompletedViews([]);
        setLastCapturedImage(null);
        setAwaitingSelection(false);
        setShowManualMarker(false);
        setManualLandmarksByView({});
        setCurrentView('front');
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
        setIsEditingMarkings(false);
        clearInterval(captureTimerRef.current);
        captureTimerRef.current = null;
        setCaptureCountdown(null);
        socket.emit('reset_session');
    };


    // Core capture logic shared by both auto and manual triggers
    const doCapture = useCallback((view) => {
        if (!webcamRef.current) return;
        const imageSrc = webcamRef.current.getScreenshot();
        if (!imageSrc) return;

        setCapturedImages(prev => ({ ...prev, [view]: imageSrc }));
        setCapturedRawImages(prev => ({ ...prev, [view]: imageSrc }));
        setCompletedViews(prev => [...new Set([...prev, view])]);
        setCameraActive(false);
        setAlignment('red');

        const currentIndex = VIEW_ORDER.indexOf(view);
        if (currentIndex < 3) {
            const nextView = VIEW_ORDER[currentIndex + 1];
            speak(`${view} captured. Now turn to show your ${nextView}.`);
            setTimeout(() => {
                setCurrentView(nextView);
                setCameraActive(true);
            }, 600);
        } else {
            setIsReviewing(true);
            speak('All views captured. Please review your photos.');
        }
    }, [VIEW_ORDER]);

    // Auto-capture is triggered from the countdown useEffect
    // Uses currentViewRef to avoid stale closures inside timer
    const triggerAutoCapture = useCallback(() => {
        doCapture(currentViewRef.current);
    }, [doCapture]);

    const handleManualCapture = () => {
        doCapture(currentView);
    };

    const handleRetakeView = (view) => {
        setCurrentView(view);
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

    const handleRetake = () => {
        setAwaitingSelection(false);
        setLastCapturedImage(null);
        setInstruction('Align yourself in the frame');
        setAlignment('red');
        socket.emit('retake_view', { view: currentView });
    };

    const handleAutomaticMarking = () => {
        setAwaitingSelection(false);
        setMarkingMode('auto');
        setMarkingViewIndex(0);
        markingModeRef.current = 'auto';
        markingViewIndexRef.current = 0;
        processNextAutoView(0);
    };

    const processNextAutoView = (index) => {
        const view = VIEW_ORDER[index];
        setProcessing(true);
        setInstruction(`Processing photo ${index + 1} of 4...`);
        setAutoProgress(prev => ({ ...prev, [view]: 'processing' }));
        
        socket.emit('process_selection', {
            view: view,
            image: capturedImages[view],
            type: 'auto',
            user_height: parseFloat(userHeight),
            height_unit: heightUnit
        });
    };

    const handleManualMarking = () => {
        setAwaitingSelection(false);
        setIsEditingMarkings(false);
        setMarkingMode('manual');
        setMarkingViewIndex(0);
        markingModeRef.current = 'manual';
        markingViewIndexRef.current = 0;
        setShowManualMarker(true);
    };

    const handleEditMarkings = () => {
        setAwaitingSelection(false);
        setIsReviewing(false);
        setIsEditingMarkings(true);
        setMarkingMode('manual');
        setMarkingViewIndex(0);
        markingModeRef.current = 'manual';
        markingViewIndexRef.current = 0;
        setShowManualMarker(true);
        setInstruction('Edit your markings and recalculate measurements.');
    };

    const getNextManualLabel = () => {
        if (markingViewIndex === 0) return 'Next: Right ->';
        if (markingViewIndex === 1) return 'Next: Back ->';
        if (markingViewIndex === 2) return 'Next: Left ->';
        return isEditingMarkings ? 'Recalculate ->' : 'Finish & Calculate ->';
    };

    const getPreviousManualLabel = () => {
        if (markingViewIndex === 1) return '<- Front';
        if (markingViewIndex === 2) return '<- Right';
        if (markingViewIndex === 3) return '<- Back';
        return '<- Previous';
    };

    const handleManualPrevious = () => {
        if (markingViewIndex <= 0) {
            return;
        }

        const prevIndex = markingViewIndex - 1;
        setMarkingViewIndex(prevIndex);
        markingViewIndexRef.current = prevIndex;
        setShowManualMarker(true);
    };

    const handleManualLandmarkComplete = (data) => {
        const activeIndex = markingViewIndexRef.current;
        const activeView = VIEW_ORDER[activeIndex];

        // We will emit the manual landmarks for this view
        setProcessing(true);
        setInstruction(`Saving landmarks for ${activeView}...`);

        socket.emit('process_selection', {
            view: activeView,
            image: capturedImages[activeView],
            type: 'manual',
            landmarks: data.landmarks,
            user_height: parseFloat(userHeight),
            height_unit: heightUnit
        });
        
        // The selection_processed listener will handle moving to the next view
    };

    useEffect(() => {
        if (!socket) return;

        socket.on('selection_processed', (data) => {
            console.log('Selection processed:', data);
            setProcessing(false);
            
            if (data.error) {
                setErrorMsg(data.error);
                setInstruction(`Detection Failed for ${data.view}`);
                setAutoProgress(prev => ({ ...prev, [data.view]: 'error' }));
                return;
            }

            setAutoProgress(prev => ({ ...prev, [data.view]: 'done' }));

            // Keep raw captured photos intact for re-editing.

            // Move to next view in sequence
            const currentIndex = markingViewIndexRef.current;
            const nextIndex = currentIndex + 1;
            if (nextIndex < 4) {
                setMarkingViewIndex(nextIndex);
                markingViewIndexRef.current = nextIndex;
                if (markingModeRef.current === 'auto') {
                    processNextAutoView(nextIndex);
                } else {
                    // For manual, we wait for user to be ready?
                    // Or just show the next marker immediately
                    setShowManualMarker(true);
                }
            } else {
                setInstruction('All views complete!');
                setProcessing(true);
                setInstruction('Finalizing analysis...');
                socket.emit('finalize_session');
            }
        });

        return () => socket.off('selection_processed');
    }, [socket, currentView, capturedImages, userHeight, heightUnit]);

    const handleUserMedia = () => {
        console.log('Camera started successfully');
        setCameraStatus('ready');
    };

    const handleUserMediaError = (error) => {
        console.error('Camera error:', error);
        setCameraStatus('error');
        
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            setCameraErrorMsg('Camera permission denied. Go to browser settings and allow camera access.');
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
            setCameraErrorMsg('Camera is being used by another application. Please close it and try again.');
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            setCameraErrorMsg('No camera device found. Please connect a camera and try again.');
        } else {
            setCameraErrorMsg('Your browser does not support camera access. Please use Chrome or Firefox.');
        }
    };

    if (results && !isEditingMarkings) {
        return (
            <div className="live-camera-results">
                <h2>Measurement Results</h2>

                <div className="results-grid">
                    {Object.entries(results.results).map(([view, data]) => (
                        <div key={view} className="view-result">
                            <h3>{view.charAt(0).toUpperCase() + view.slice(1)} View</h3>

                            <div className="images-row">
                                {data.original_image && (
                                    <div className="image-container">
                                        <p>Original</p>
                                        <img src={data.original_image} alt={`${view} original`} />
                                    </div>
                                )}
                                {data.mask && (
                                    <div className="image-container">
                                        <p>Masked</p>
                                        <img src={data.mask} alt={`${view} mask`} />
                                    </div>
                                )}
                                {data.visualization && (
                                    <div className="image-container">
                                        <p>Landmarks</p>
                                        <img src={data.visualization} alt={`${view} landmarks`} />
                                    </div>
                                )}
                            </div>

                            {data.measurements && (
                                <div className="measurements-list">
                                    <h4>Measurements</h4>
                                    <table className="measurements-table">
                                        <thead>
                                            <tr>
                                                <th>Measurement</th>
                                                <th>Value (cm)</th>
                                                <th>Value (px)</th>
                                                <th>Source</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {Object.entries(data.measurements).map(([key, m]) => (
                                                <tr key={key}>
                                                    <td>{m.label || key.replace(/_/g, ' ')}</td>
                                                    <td>{m.value_cm} cm</td>
                                                    <td>{m.value_px} px</td>
                                                    <td>{m.source || 'Auto'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                <div className="results-actions-row">
                    <button onClick={handleEditMarkings} className="edit-markings-button">
                        ✏ Edit Markings
                    </button>
                    <button onClick={resetSession} className="reset-button">Start New Session</button>
                </div>
            </div>
        );
    }

    if (showManualMarker) {
        const currentMarkingView = VIEW_ORDER[markingViewIndex];
        const imageData =
            capturedRawImages[currentMarkingView] ||
            capturedImages[currentMarkingView] ||
            results?.results?.[currentMarkingView]?.original_image;
        
        return (
            <div className="manual-marker-wrapper">
                <div className="marking-progress-header">
                    <h3>Manual Marking: {currentMarkingView.charAt(0).toUpperCase() + currentMarkingView.slice(1)} View</h3>
                    <div className="progress-badge">Marking {markingViewIndex + 1} of 4</div>
                </div>
                <ManualLandmarkMarker
                    key={currentMarkingView}
                    imageData={imageData}
                    imageType={currentMarkingView}
                    initialLandmarks={manualLandmarksByView[currentMarkingView] || emptyLandmarksRef.current}
                    onLandmarksChange={(updatedLandmarks) => {
                        setManualLandmarksByView(prev => ({
                            ...prev,
                            [currentMarkingView]: updatedLandmarks
                        }));
                    }}
                    onPrevious={markingViewIndex > 0 ? handleManualPrevious : null}
                    previousLabel={getPreviousManualLabel()}
                    nextLabel={getNextManualLabel()}
                    onComplete={handleManualLandmarkComplete}
                    onCancel={() => {
                        setShowManualMarker(false);
                        setMarkingMode(null);
                        setAwaitingSelection(true);
                    }}
                    onReset={() => {
                        setManualLandmarksByView(prev => ({
                            ...prev,
                            [currentMarkingView]: []
                        }));
                    }}
                />
            </div>
        );
    }

    if (awaitingSelection) {
        return (
            <div className="live-camera-selection">
                <div className="selection-content">
                    <h2>Choose marking method</h2>
                    <p>All 4 views captured. How would you like to proceed?</p>
                    
                    <div className="captured-preview-grid">
                        {VIEW_ORDER.map(view => (
                            <div key={view} className="preview-tile">
                                <img src={capturedImages[view]} alt={`${view} preview`} />
                                <span>{view.charAt(0).toUpperCase() + view.slice(1)}</span>
                            </div>
                        ))}
                    </div>
                    
                    {errorMsg && (
                        <div className="error-message">
                            <p>{errorMsg}</p>
                            <p>Please retake failing photos or use Manual Marking.</p>
                        </div>
                    )}

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

                    <button onClick={resetSession} className="retake-button" disabled={processing}>
                        Reset and Restart
                    </button>
                </div>
            </div>
        );
    }

    if (markingMode === 'auto') {
        return (
            <div className="auto-processing-container">
                <h2>Automatic Marking</h2>
                <div className="processing-grid">
                    {VIEW_ORDER.map((view, index) => {
                        const status = autoProgress[view];
                        return (
                            <div key={view} className={`processing-tile ${status || ''}`}>
                                <div className="tile-image">
                                    <img src={capturedImages[view]} alt={view} />
                                    {status === 'processing' && <div className="processing-overlay"><div className="spinner-small"></div></div>}
                                    {status === 'done' && <div className="status-overlay success">✓</div>}
                                    {status === 'error' && <div className="status-overlay error">✗</div>}
                                </div>
                                <div className="view-label">
                                    {view.charAt(0).toUpperCase() + view.slice(1)}
                                    {status === 'error' && (
                                        <button 
                                            className="single-retake-btn"
                                            onClick={() => {
                                                setMarkingMode(null);
                                                setCurrentView(view);
                                                setCaptureSequenceComplete(false);
                                                setAutoProgress(prev => {
                                                    const next = { ...prev };
                                                    delete next[view];
                                                    return next;
                                                });
                                                setInstruction(`Retaking ${view} view`);
                                            }}
                                        >
                                            Retake
                                        </button>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
                <div className="overall-status">
                    {markingViewIndex < 4 ? `Processing photo ${markingViewIndex + 1} of 4...` : 'Finalizing analysis...'}
                </div>
                {errorMsg && <div className="error-message">{errorMsg}</div>}
            </div>
        );
    }

    if (isReviewing) {
        return (
            <div className="camera-review-screen">
                <h2>All photos captured</h2>
                <div className="review-grid-row">
                    {VIEW_ORDER.map(view => (
                        <div key={view} className="review-thumb">
                            <div className="thumb-wrapper">
                                <img src={capturedImages[view]} alt={view} />
                            </div>
                            <span className="thumb-label">{view.charAt(0).toUpperCase() + view.slice(1)} View</span>
                            <button onClick={() => handleRetakeView(view)} className="mini-retake-btn">
                                Retake
                            </button>
                        </div>
                    ))}
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
                <div className={`camera-view ${alignment}`}>
                    <div className="camera-header-tabs">
                        {VIEW_ORDER.map((view, idx) => (
                            <div key={view} className={`tab-item ${currentView === view ? 'active' : ''} ${completedViews.includes(view) ? 'completed' : ''}`}>
                                {completedViews.includes(view) && <span className="check">✓</span>}
                                {view.toUpperCase()}
                            </div>
                        ))}
                    </div>

                    <div className="view-instruction-overlay">
                        <h2>{markingViewIndex + 1} of 4 — {currentView.charAt(0).toUpperCase() + currentView.slice(1)} {currentView === 'right' || currentView === 'left' ? 'Side ' : ''}View</h2>
                        <p>{currentView === 'front' ? 'Stand facing the camera' : 
                            currentView === 'right' ? 'Turn to show your right side' :
                            currentView === 'back' ? 'Turn to show your back' :
                            'Turn to show your left side'}</p>
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

                        <SilhouetteOverlay view={currentView} />

                        {/* Auto-capture countdown overlay */}
                        {alignment === 'green' && captureCountdown !== null && (
                            <div className="auto-capture-overlay">
                                <div className="countdown-ring">
                                    <svg viewBox="0 0 100 100">
                                        <circle cx="50" cy="50" r="42" className="countdown-bg" />
                                        <circle
                                            cx="50" cy="50" r="42"
                                            className="countdown-progress"
                                            strokeDasharray={`${(( captureCountdown / 3) * 263.9).toFixed(1)} 263.9`}
                                        />
                                    </svg>
                                    <span className="countdown-number">{captureCountdown}</span>
                                </div>
                                <p className="auto-capture-hint">Hold still…</p>
                            </div>
                        )}

                        {/* Green alignment pulse when aligned, but countdown not started yet */}
                        {alignment === 'green' && captureCountdown === null && (
                            <div className="alignment-good-hint">✓ Aligned</div>
                        )}

                        {/* Misaligned hint */}
                        {alignment === 'red' && cameraActive && (
                            <div className="alignment-hint-text">Align yourself in the frame</div>
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
                                    facingMode: "user"
                                }}
                                style={{
                                    visibility: cameraStatus === 'ready' ? 'visible' : 'hidden'
                                }}
                            />
                        )}
                    </div>

                    <div className="camera-controls">
                        <button onClick={handleManualCapture} className="capture-btn-main">
                            <div className="capture-inner"></div>
                        </button>
                        <button onClick={resetSession} className="cancel-text-btn">Cancel</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LiveCamera;
