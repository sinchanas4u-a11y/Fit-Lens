import React, { useState, useEffect, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import io from 'socket.io-client';
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
            setCurrentView(data.next_view);

            // Always speak the voice message from backend
            if (data.voice_message) {
                speak(data.voice_message);
            }

            if (data.next_view === 'complete') {
                setProcessing(true);
                setInstruction('Processing all views...');
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
        speak('Please face the front.');
    };

    const resetSession = () => {
        setSessionStarted(false);
        setCapturedImages({});
        setCurrentView('front');
        setResults(null);
        setProcessing(false);
        setInstruction('Align yourself in the frame');
        setAlignment('red');
        socket.emit('reset_session');
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
                                    <ul>
                                        {Object.entries(data.measurements).map(([key, m]) => (
                                            <li key={key}>
                                                <strong>{key.replace(/_/g, ' ')}:</strong> {m.value_cm} cm
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                <button onClick={resetSession} className="reset-button">Start New Session</button>
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
                        {countdown !== null && <div className="countdown">{countdown}</div>}
                    </div>

                    <Webcam
                        ref={webcamRef}
                        audio={false}
                        screenshotFormat="image/jpeg"
                        width={640}
                        height={480}
                        videoConstraints={{
                            facingMode: "user"
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
