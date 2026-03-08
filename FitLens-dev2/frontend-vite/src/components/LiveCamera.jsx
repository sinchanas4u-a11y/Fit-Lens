import React, { useState, useEffect, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import io from 'socket.io-client';
import ManualLandmarkMarker from './ManualLandmarkMarker';
import './LiveCamera.css';

const LiveCamera = () => {
    const webcamRef = useRef(null);
    const [socket, setSocket] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [alignment, setAlignment] = useState('red');
    const [instruction, setInstruction] = useState('Connecting to camera...');
    const [countdown, setCountdown] = useState(null);
    const [currentView, setCurrentView] = useState('front');
    const [capturedImages, setCapturedImages] = useState({});
    const [processing, setProcessing] = useState(false);
    const [results, setResults] = useState(null);
    const [userHeight, setUserHeight] = useState('');
    const [heightUnit, setHeightUnit] = useState('cm');
    const [sessionStarted, setSessionStarted] = useState(false);
    
    // Selection state
    const [awaitingSelection, setAwaitingSelection] = useState(false);
    const [lastCapturedImage, setLastCapturedImage] = useState(null);
    const [showManualMarker, setShowManualMarker] = useState(false);
    const [errorMsg, setErrorMsg] = useState(null);
    const [cameraStatus, setCameraStatus] = useState('initializing'); // 'initializing', 'ready', 'error'
    const [cameraErrorMsg, setCameraErrorMsg] = useState(null);
    
    // New Workflow state
    const VIEW_ORDER = ['front', 'right', 'back', 'left'];
    const [captureSequenceComplete, setCaptureSequenceComplete] = useState(false);
    const [markingMode, setMarkingMode] = useState(null); // 'manual' | 'auto'
    const [markingViewIndex, setMarkingViewIndex] = useState(0);
    const [autoProgress, setAutoProgress] = useState({}); // {front: 'done', right: 'processing', ...}

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
            setLastCapturedImage(data.image);
            
            if (data.next_view === 'complete') {
                setCaptureSequenceComplete(true);
                setAwaitingSelection(true);
                setInstruction('Choose marking method');
                speak('All views captured. Please choose a marking method.');
            } else {
                setCurrentView(data.next_view);
                setInstruction(`Turn to ${data.next_view} view`);
                
                // Speak the capture confirmation and next view instruction
                if (data.voice_message) {
                    speak(data.voice_message);
                }
            }
        });

        newSocket.on('processing_complete', (data) => {
            console.log('Processing complete:', data);
            setResults(data);
            setProcessing(false);
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
        if (!sessionStarted || !isConnected || !socket) return;

        const interval = setInterval(() => {
            captureAndSendFrame();
        }, 200); // 5 FPS

        return () => clearInterval(interval);
    }, [sessionStarted, isConnected, socket, currentView, userHeight, heightUnit]);

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
        setCameraStatus('initializing');
        setCameraErrorMsg(null);
        speak('Please face the front.');
    };

    const resetSession = () => {
        setSessionStarted(false);
        setCapturedImages({});
        setLastCapturedImage(null);
        setAwaitingSelection(false);
        setShowManualMarker(false);
        setCurrentView('front');
        setResults(null);
        setProcessing(false);
        setErrorMsg(null);
        setInstruction('Align yourself in the frame');
        setAlignment('red');
        setCameraStatus('initializing');
        setCameraErrorMsg(null);
        setCaptureSequenceComplete(false);
        setMarkingMode(null);
        setMarkingViewIndex(0);
        setAutoProgress({});
        socket.emit('reset_session');
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
        setMarkingMode('manual');
        setMarkingViewIndex(0);
        setShowManualMarker(true);
    };

    const handleManualLandmarkComplete = (data) => {
        // We will emit the manual landmarks for this view
        setProcessing(true);
        setInstruction(`Saving landmarks for ${VIEW_ORDER[markingViewIndex]}...`);

        socket.emit('process_selection', {
            view: VIEW_ORDER[markingViewIndex],
            image: capturedImages[VIEW_ORDER[markingViewIndex]],
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

            // Update captured images with visualization if provided
            setCapturedImages(prev => ({
                ...prev,
                [data.view]: data.visualization || prev[data.view]
            }));

            // Move to next view in sequence
            const nextIndex = markingViewIndex + 1;
            if (nextIndex < 4) {
                setMarkingViewIndex(nextIndex);
                if (markingMode === 'auto') {
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
    }, [socket, currentView]);

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

    if (results) {
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

                <button onClick={resetSession} className="reset-button">Start New Session</button>
            </div>
        );
    }

    if (showManualMarker) {
        const currentMarkingView = VIEW_ORDER[markingViewIndex];
        const imageData = capturedImages[currentMarkingView];
        
        return (
            <div className="manual-marker-wrapper">
                <div className="marking-progress-header">
                    <h3>Manual Marking: {currentMarkingView.charAt(0).toUpperCase() + currentMarkingView.slice(1)} View</h3>
                    <div className="progress-badge">Marking {markingViewIndex + 1} of 4</div>
                </div>
                <ManualLandmarkMarker
                    imageData={imageData}
                    imageType={currentMarkingView}
                    onComplete={handleManualLandmarkComplete}
                    onCancel={() => {
                        setShowManualMarker(false);
                        setMarkingMode(null);
                        setAwaitingSelection(true);
                    }}
                    onReset={() => {}}
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
                    <div className="overlay-header">
                        <h3>{instruction}</h3>
                        <div className="height-reference">
                            Reference Height: <strong>{userHeight} {heightUnit}</strong>
                        </div>
                        {countdown !== null && <div className="countdown">{countdown}</div>}
                    </div>

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

                    <div className="overlay-footer">
                        <div className="step-indicator">
                            <span className={currentView === 'front' ? 'active' : capturedImages.front ? 'completed' : ''}>Front</span>
                            <span className={currentView === 'right' ? 'active' : capturedImages.right ? 'completed' : ''}>Right</span>
                            <span className={currentView === 'back' ? 'active' : capturedImages.back ? 'completed' : ''}>Back</span>
                            <span className={currentView === 'left' ? 'active' : capturedImages.left ? 'completed' : ''}>Left</span>
                        </div>
                        <button onClick={resetSession} className="cancel-button">Cancel</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LiveCamera;
