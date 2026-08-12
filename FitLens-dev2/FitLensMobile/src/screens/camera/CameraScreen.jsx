import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Image,
  TextInput,
  ScrollView,
} from 'react-native';
import { Camera, useCameraDevice } from 'react-native-vision-camera';
import Svg, { Circle, Line } from 'react-native-svg';
import io from 'socket.io-client';
import RNFS from 'react-native-fs';
import Tts from 'react-native-tts';
import { Config } from '../../constants/config';
import ManualLandmarkModal from '../../components/measurement/ManualLandmarkModal';
import ZoomableImageModal from '../../components/common/ZoomableImageModal';
import { measurementApi } from '../../api/measurementApi';

const CameraScreen = ({ navigation }) => {
  const [hasPermission, setHasPermission] = useState(false);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [currentView, setCurrentView] = useState('front'); // 'front' | 'side'

  // Alignment & Countdown states (Server-driven via Socket.IO)
  const [isAligned, setIsAligned] = useState(false);
  const isAlignedRef = useRef(false);
  const countdownRef = useRef(null);
  const countdownValueRef = useRef(3);
  const [countdown, setCountdown] = useState(null);

  // Captured Images State
  const [capturedImages, setCapturedImages] = useState({ front: null, side: null });
  const [isReviewing, setIsReviewing] = useState(false);
  const [userHeight, setUserHeight] = useState('165');
  const [processingManual, setProcessingManual] = useState(false);

  // Zoom modal state
  const [zoomImageUri, setZoomImageUri] = useState(null);
  const [zoomTitle, setZoomTitle] = useState('');

  // Manual Marking Modal state
  const [manualModalVisible, setManualModalVisible] = useState(false);
  const [manualViewStep, setManualViewStep] = useState('front');
  const [manualLandmarks, setManualLandmarks] = useState({ front: null, side: null });

  // Alignment instruction state
  const [alignmentData, setAlignmentData] = useState({
    alignment: 'red',
    instruction: 'Stand facing camera in A-pose',
    countdown: null,
    speak: false,
  });

  const cameraRef = useRef(null);
  const socketRef = useRef(null);
  const handlersAttachedRef = useRef(false);
  const isProcessingFrameRef = useRef(false);
  const isCapturingPhotoRef = useRef(false);
  const frameIntervalRef = useRef(null);
  const lastSpokenRef = useRef('');

  const isConnectedRef = useRef(false);
  const isCameraReadyRef = useRef(false);
  const hasPermissionRef = useRef(false);
  const currentViewRef = useRef('front');

  const [cameraPosition, setCameraPosition] = useState('front'); // 'front' | 'back'

  useEffect(() => { isConnectedRef.current = isConnected; }, [isConnected]);
  useEffect(() => { isCameraReadyRef.current = isCameraReady; }, [isCameraReady]);
  useEffect(() => { hasPermissionRef.current = hasPermission; }, [hasPermission]);
  useEffect(() => { currentViewRef.current = currentView; }, [currentView]);

  const backDevice = useCameraDevice('back');
  const frontDevice = useCameraDevice('front');
  const device = cameraPosition === 'front' ? (frontDevice || backDevice) : (backDevice || frontDevice);

  const flipCamera = () => {
    setCameraPosition(prev => (prev === 'front' ? 'back' : 'front'));
    isAlignedRef.current = false;
    setIsAligned(false);
    stopCountdown();
  };

  // Test backend connection on mount
  useEffect(() => {
    fetch(`${Config.BASE_URL}/api/health`)
      .then(r => r.json())
      .then(d => console.log('[Health] Backend OK:', d))
      .catch(e => console.log('[Health] Backend UNREACHABLE:', e.message, '\nCheck: same WiFi? IP correct?', Config.BASE_URL));
  }, []);

  // Safe TTS helper that handles missing/unlinked native modules gracefully
  const isTtsAvailable = () => {
    try {
      return Boolean(Tts && typeof Tts.speak === 'function' && typeof Tts.setDefaultLanguage === 'function');
    } catch {
      return false;
    }
  };

  // Initialize TTS safely
  useEffect(() => {
    if (isTtsAvailable()) {
      try {
        Tts.setDefaultLanguage('en-US');
        Tts.setDefaultRate(0.5);
      } catch (err) {
        console.warn('[TTS] Init warning:', err?.message || err);
      }
    } else {
      console.warn('[TTS] Text-To-Speech native module is unavailable. Voice guidance disabled.');
    }

    return () => {
      if (isTtsAvailable()) {
        try { Tts.stop(); } catch (e) {}
      }
    };
  }, []);

  const speakInstruction = (text) => {
    if (!text || text === lastSpokenRef.current) return;
    lastSpokenRef.current = text;
    if (isTtsAvailable()) {
      try {
        Tts.stop();
        Tts.speak(text);
      } catch (err) {
        console.warn('[TTS] Speech warning:', err?.message || err);
      }
    }
  };

  // Request camera permission
  useEffect(() => {
    (async () => {
      try {
        const permission = await Camera.requestCameraPermission();
        setHasPermission(permission === 'granted');
        if (permission !== 'granted') {
          Alert.alert(
            'Camera Permission Required',
            'FitLens needs camera access to perform live body alignment.',
            [{ text: 'Go Back', onPress: () => navigation.goBack() }]
          );
        }
      } catch (err) {
        console.error('Failed to request camera permission:', err);
      }
    })();
  }, [navigation]);

  // Fix 1 — Connect to backend via Socket.IO (Singleton pattern)
  useEffect(() => {
    if (socketRef.current) return; // Socket already created, skip duplicate instantiation

    console.log('[CameraScreen] Connecting to Socket.IO backend at:', Config.BASE_URL);
    const socket = io(Config.BASE_URL, {
      transports: ['websocket', 'polling'], // Prefer WebSocket in React Native for zero-latency
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
      forceNew: false,
      autoConnect: true,
    });
    socketRef.current = socket;

    if (!handlersAttachedRef.current) {
      handlersAttachedRef.current = true;

      socket.on('connect', () => {
        console.log('✅ Socket connected:', socket.id);
        setIsConnected(true);
        isProcessingFrameRef.current = false;
      });

      socket.on('disconnect', (reason) => {
        console.log('⚠️ Socket disconnected:', reason);
        setIsConnected(false);
        isProcessingFrameRef.current = false;
        if (reason === 'io server disconnect') {
          // Server closed connection intentionally, reconnect manually if needed
          socket.connect();
        }
      });

      socket.on('connect_error', (err) => {
        console.log('❌ Socket connect error:', err.message);
        isProcessingFrameRef.current = false;
      });

      socket.on('frame_processed', (data) => {
        isProcessingFrameRef.current = false;
        if (!data) return;

        const aligned = data.alignment === 'green';
        setIsAligned(aligned);
        isAlignedRef.current = aligned;

        setAlignmentData({
          alignment: data.alignment || 'red',
          instruction: data.instruction || 'Align your body with the silhouette guide',
          countdown: data.countdown ?? null,
          speak: data.speak || false,
        });

        setCountdown(data.countdown ?? null);

        if (data.speak && data.instruction) {
          speakInstruction(data.instruction);
        }

        if (aligned && data.countdown === 0 && !isCapturingPhotoRef.current) {
          executeCapturePhoto();
        }
      });
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
        handlersAttachedRef.current = false;
      }
    };
  }, []); // Runs ONCE on mount

  // Frame streaming over socket (optional background telemetry) — throttled to prevent JS bridge blocking
  useEffect(() => {
    if (!isCameraReady || !hasPermission || !isConnected || isReviewing) {
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
        frameIntervalRef.current = null;
      }
      return;
    }

    // Keep Socket.IO connection stable by omitting heavy base64 streaming during alignment check
    // Alignment is handled 100% reliably via REST polling /validate/person-count
  }, [isCameraReady, hasPermission, isConnected, isReviewing]);

  // Fix 2 — Alignment check via direct REST polling (/validate/person-count)
  // Works in OFFLINE mode without socket requirement!
  const alignmentCheckRef = useRef(null);

  const stopAlignmentChecking = useCallback(() => {
    if (alignmentCheckRef.current) {
      clearInterval(alignmentCheckRef.current);
      alignmentCheckRef.current = null;
    }
  }, []);

  const startAlignmentChecking = useCallback(() => {
    stopAlignmentChecking();

    alignmentCheckRef.current = setInterval(async () => {
      if (
        !cameraRef.current ||
        isCapturingPhotoRef.current ||
        !isCameraReadyRef.current ||
        !hasPermissionRef.current
      ) {
        return;
      }

      try {
        let photo;
        if (typeof cameraRef.current.takeSnapshot === 'function') {
          photo = await cameraRef.current.takeSnapshot({ quality: 50 });
        } else {
          photo = await cameraRef.current.takePhoto({ qualityPrioritization: 'speed', flash: 'off' });
        }

        const cleanPath = photo.path.replace('file://', '');
        const photoUri = `file://${cleanPath}`;

        const formData = new FormData();
        formData.append('image', {
          uri: photoUri,
          type: 'image/jpeg',
          name: 'validation_frame.jpg',
        });
        formData.append('view', currentViewRef.current);

        const response = await fetch(`${Config.BASE_URL}/validate/person-count`, {
          method: 'POST',
          body: formData,
        });

        const responseText = await response.text();
        RNFS.unlink(cleanPath).catch(() => {});

        let data;
        try {
          data = JSON.parse(responseText);
        } catch {
          return;
        }

        const personDetected = data.success === true;

        if (personDetected && !isAlignedRef.current) {
          console.log('[Alignment] ✅ Person aligned — turning GREEN');
          isAlignedRef.current = true;
          setIsAligned(true);
          setAlignmentData(prev => ({
            ...prev,
            alignment: 'green',
            instruction: 'Hold still! Auto-capturing...',
          }));
          startCountdown();
        } else if (!personDetected) {
          if (isAlignedRef.current) {
            console.log('[Alignment] ❌ Person lost — turning RED');
            isAlignedRef.current = false;
            setIsAligned(false);
            stopCountdown();
          }
          let serverError = data?.error || (currentViewRef.current === 'front'
            ? 'Stand facing camera in A-pose (head to toe)'
            : 'Turn 90° to your right for side view');
          if (serverError.includes('full-body') || serverError.includes('Cropped')) {
            serverError = 'Step back 6-8 ft so full body (head to toe) is visible';
          }
          setAlignmentData(prev => ({
            ...prev,
            alignment: 'red',
            instruction: serverError,
          }));
        }
      } catch (err) {
        console.log('[Alignment Check] Error:', err.message);
      }
    }, 2500);
  }, []);

  // Fix 2: Start alignment checking as soon as camera is ready (does NOT depend on isConnected):
  useEffect(() => {
    if (isCameraReady && hasPermission && !isReviewing) {
      console.log('[Alignment] Camera ready — starting alignment check');
      startAlignmentChecking();
    }
    return () => {
      stopAlignmentChecking();
      stopCountdown();
    };
  }, [isCameraReady, hasPermission, isReviewing, startAlignmentChecking]);

  const startCountdown = () => {
    if (countdownRef.current) return;
    countdownValueRef.current = 3;
    setCountdown(3);
    console.log('[Countdown] Starting 3-2-1...');

    countdownRef.current = setInterval(() => {
      if (!isAlignedRef.current) {
        console.log('[Countdown] Person misaligned — stopping countdown');
        stopCountdown();
        return;
      }

      countdownValueRef.current -= 1;
      setCountdown(countdownValueRef.current);

      if (isTtsAvailable() && countdownValueRef.current > 0) {
        try { Tts.speak(String(countdownValueRef.current)); } catch {}
      }

      if (countdownValueRef.current <= 0) {
        console.log('[Countdown] Reached 0 — capturing photo');
        stopCountdown();
        stopAlignmentChecking();
        executeCapturePhoto();
      }
    }, 1000);
  };

  const stopCountdown = () => {
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
    countdownValueRef.current = 3;
    setCountdown(null);
  };

  // Reset alignment state when view changes
  useEffect(() => {
    if (isCameraReady && hasPermission && !isReviewing) {
      isAlignedRef.current = false;
      setIsAligned(false);
      stopCountdown();
      setCountdown(null);
      setAlignmentData({
        alignment: 'red',
        instruction: currentView === 'front'
          ? 'Stand facing camera in A-pose'
          : 'Turn 90° to your right for side view',
        countdown: null,
        speak: false,
      });
      setTimeout(() => startAlignmentChecking(), 500);
    }
  }, [currentView, isCameraReady, hasPermission, isReviewing, startAlignmentChecking]);

  // Store front and side captures separately:
  const executeCapturePhoto = async () => {
    if (isCapturingPhotoRef.current || !cameraRef.current) return;
    isCapturingPhotoRef.current = true;

    try {
      if (isTtsAvailable()) {
        try { Tts.stop(); } catch {}
      }

      const photo = await cameraRef.current.takePhoto({
        qualityPrioritization: 'quality',
        flash: 'off',
      });

      // CRITICAL — use file:// prefix:
      const uri = `file://${photo.path}`;
      console.log(`[Capture] ${currentViewRef.current} photo URI:`, uri);

      if (currentViewRef.current === 'front') {
        // Store front image:
        setCapturedImages(prev => {
          const updated = { ...prev, front: uri };
          console.log('[Capture] Updated capturedImages:', updated);
          return updated;
        });

        if (isTtsAvailable()) {
          try { Tts.speak('Front view captured! Now turn 90 degrees to your right.'); } catch {}
        }

        // Switch to side view after 2 seconds:
        setTimeout(() => {
          isCapturingPhotoRef.current = false;
          isAlignedRef.current = false;
          setIsAligned(false);
          setCountdown(null);
          setCurrentView('side');
          currentViewRef.current = 'side';
        }, 2000);

      } else {
        // Store side image — DIFFERENT from front:
        setCapturedImages(prev => {
          const updated = { ...prev, side: uri };
          console.log('[Capture] Updated capturedImages:', updated);
          return updated;
        });

        if (isTtsAvailable()) {
          try { Tts.speak('Side view captured! Processing measurements.'); } catch {}
        }

        // Show review screen:
        setTimeout(() => {
          isCapturingPhotoRef.current = false;
          stopCountdown();
          if (isTtsAvailable()) { try { Tts.stop(); } catch {} }
          setIsReviewing(true);
        }, 1500);
      }
    } catch (err) {
      console.log('[Capture] Error:', err.message);
      isCapturingPhotoRef.current = false;
      isAlignedRef.current = false;
      setIsAligned(false);
      stopCountdown();
      startAlignmentChecking();
    }
  };

  // Cleanup on unmount:
  useEffect(() => {
    return () => {
      stopCountdown();
      if (isTtsAvailable()) { try { Tts.stop(); } catch {} }
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  const handleRetakeView = (viewToRetake) => {
    setCapturedImages((prev) => ({ ...prev, [viewToRetake]: null }));
    setCurrentView(viewToRetake);
    currentViewRef.current = viewToRetake;
    setIsReviewing(false);
    isAlignedRef.current = false;
    setIsAligned(false);
    stopCountdown();
    setCountdown(null);
    setAlignmentData({
      alignment: 'red',
      instruction: `Align yourself for ${viewToRetake} view`,
      countdown: null,
      speak: false,
    });
    speakInstruction(`Retaking ${viewToRetake} view. Align yourself in frame.`);
    setTimeout(() => startAlignmentChecking(), 500);
  };

  const handleAutomaticMode = async () => {
    if (!capturedImages.front || !capturedImages.side) {
      Alert.alert('Missing Photos', 'Both front and side photos required');
      return;
    }

    try {
      // Convert file URIs to base64:
      const frontBase64Raw = await RNFS.readFile(
        capturedImages.front.replace('file://', ''), 'base64');
      const sideBase64Raw = await RNFS.readFile(
        capturedImages.side.replace('file://', ''), 'base64');

      const frontBase64 = `data:image/jpeg;base64,${frontBase64Raw}`;
      const sideBase64 = `data:image/jpeg;base64,${sideBase64Raw}`;

      console.log('[Process] Front base64 length:', frontBase64.length);
      console.log('[Process] Side base64 length:', sideBase64.length);

      navigation.navigate('Processing', {
        frontImageUri: capturedImages.front,
        sideImageUri: capturedImages.side,
        frontBase64,
        sideBase64,
        userHeightCm: parseFloat(userHeight) || 165,
      });
    } catch (err) {
      console.log('[Process] Conversion error:', err.message);
      Alert.alert('Error', 'Failed to prepare images: ' + err.message);
    }
  };

  const handleManualMarkingMode = () => {
    setManualLandmarks({ front: null, side: null });
    setManualViewStep('front');
    setManualModalVisible(true);
  };

  const handleManualLandmarkComplete = async (viewData) => {
    setManualModalVisible(false);

    if (manualViewStep === 'front') {
      const updatedLandmarks = { ...manualLandmarks, front: viewData };
      setManualLandmarks(updatedLandmarks);

      if (capturedImages.side) {
        Alert.alert(
          'Front View Marked ✓',
          'Now let us mark the Side View photo.',
          [
            {
              text: 'Mark Side View',
              onPress: () => {
                setManualViewStep('side');
                setManualModalVisible(true);
              },
            },
          ]
        );
      } else {
        await submitManualLandmarks(updatedLandmarks);
      }
    } else {
      const updatedLandmarks = { ...manualLandmarks, side: viewData };
      setManualLandmarks(updatedLandmarks);
      await submitManualLandmarks(updatedLandmarks);
    }
  };

  const submitManualLandmarks = async (finalLandmarks) => {
    try {
      setProcessingManual(true);
      console.log('🎯 Submitting manual landmarks to backend...');

      const frontB64 = capturedImages.front
        ? (capturedImages.front.startsWith('data:')
            ? capturedImages.front
            : `data:image/jpeg;base64,${await RNFS.readFile(capturedImages.front.replace('file://', ''), 'base64')}`)
        : null;

      const sideB64 = capturedImages.side
        ? (capturedImages.side.startsWith('data:')
            ? capturedImages.side
            : `data:image/jpeg;base64,${await RNFS.readFile(capturedImages.side.replace('file://', ''), 'base64')}`)
        : null;

      const requestPayload = {
        user_height: parseFloat(userHeight) || 165,
        front_landmarks: finalLandmarks.front || null,
        side_landmarks: finalLandmarks.side || null,
        front_image: frontB64,
        side_image: sideB64,
      };

      const res = await measurementApi.processManual(requestPayload);

      if (res.data?.success) {
        navigation.replace('Results', { data: res.data });
      } else {
        Alert.alert('Manual Processing Failed', res.data?.error || 'Could not compute measurements.');
      }
    } catch (err) {
      console.error('Camera manual processing error:', err);
      Alert.alert('Processing Failed', err.response?.data?.error || err.message || 'Error processing manual landmarks.');
    } finally {
      setProcessingManual(false);
    }
  };

  // Fix 1 & 3: Dynamic silhouette colors using explicit hex strings
  const silhouetteColor = isAligned ? '#00D4AA' : '#FF4444';
  const silhouetteFillColor = isAligned ? '#00D4AA' : '#FF4444';
  const silhouetteOpacity = 0.15;

  if (!hasPermission) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.infoText}>Camera permission is required.</Text>
        <TouchableOpacity style={styles.backBtnInline} onPress={() => navigation.goBack()}>
          <Text style={styles.backBtnText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!device) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#00D4AA" />
        <Text style={[styles.infoText, { marginTop: 12 }]}>Initializing camera device...</Text>
        <TouchableOpacity style={styles.backBtnInline} onPress={() => navigation.goBack()}>
          <Text style={styles.backBtnText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Review & Measurement Selection Screen
  if (isReviewing) {
    return (
      <ScrollView style={styles.reviewContainer} contentContainerStyle={styles.reviewContent}>
        <Text style={styles.reviewHeader}>All Photos Captured</Text>
        <Text style={styles.reviewSubheader}>Review your captured view photos below</Text>

        <View style={styles.reviewGrid}>
          {/* Front View Card */}
          <View style={styles.reviewCard}>
            <Text style={styles.cardLabel}>✓ Front View</Text>
            {capturedImages.front ? (
              <TouchableOpacity activeOpacity={0.8} onPress={() => { setZoomImageUri(capturedImages.front); setZoomTitle('Front View Photo'); }}>
                <Image
                  source={{ uri: capturedImages.front }}
                  style={styles.cardImage}
                  resizeMode="cover"
                  onLoad={() => console.log('[Image] Front loaded')}
                  onError={(e) => console.log('[Image] Front error:', e.nativeEvent.error)}
                />
              </TouchableOpacity>
            ) : (
              <View style={styles.missingImage}>
                <Text style={styles.missingText}>No image</Text>
              </View>
            )}
            <TouchableOpacity
              style={styles.retakeBtn}
              onPress={() => {
                setCapturedImages(prev => ({ ...prev, front: null }));
                setIsReviewing(false);
                setCurrentView('front');
                currentViewRef.current = 'front';
                setIsAligned(false);
                isAlignedRef.current = false;
                setCountdown(null);
                setTimeout(() => startAlignmentChecking(), 500);
              }}>
              <Text style={styles.retakeBtnText}>↺ Retake Front</Text>
            </TouchableOpacity>
          </View>

          {/* Side View Card */}
          <View style={styles.reviewCard}>
            <Text style={styles.cardLabel}>✓ Side View</Text>
            {capturedImages.side ? (
              <TouchableOpacity activeOpacity={0.8} onPress={() => { setZoomImageUri(capturedImages.side); setZoomTitle('Side View Photo'); }}>
                <Image
                  source={{ uri: capturedImages.side }}
                  style={styles.cardImage}
                  resizeMode="cover"
                  onLoad={() => console.log('[Image] Side loaded')}
                  onError={(e) => console.log('[Image] Side error:', e.nativeEvent.error)}
                />
              </TouchableOpacity>
            ) : (
              <View style={styles.missingImage}>
                <Text style={styles.missingText}>No image</Text>
              </View>
            )}
            <TouchableOpacity
              style={styles.retakeBtn}
              onPress={() => {
                setCapturedImages(prev => ({ ...prev, side: null }));
                setIsReviewing(false);
                setCurrentView('side');
                currentViewRef.current = 'side';
                setIsAligned(false);
                isAlignedRef.current = false;
                setCountdown(null);
                setTimeout(() => startAlignmentChecking(), 500);
              }}>
              <Text style={styles.retakeBtnText}>↺ Retake Side</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Height Adjustment */}
        <View style={styles.heightBox}>
          <Text style={styles.heightLabel}>Height (cm):</Text>
          <TextInput
            style={styles.heightInput}
            value={userHeight}
            onChangeText={setUserHeight}
            keyboardType="numeric"
            placeholder="165"
            placeholderTextColor="#718096"
          />
        </View>

        {/* Mode Selection Buttons */}
        <Text style={styles.methodHeader}>Choose Detection Method</Text>

        <TouchableOpacity style={styles.methodBtnAi} onPress={handleAutomaticMode}>
          <Text style={styles.methodTitle}>⚡ Automatic AI Measurement</Text>
          <Text style={styles.methodSub}>Automatic body segmentation and SMPL 3D mesh modeling</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.methodBtnManual} onPress={handleManualMarkingMode}>
          <Text style={styles.methodTitle}>✋ Manual Landmark Marking</Text>
          <Text style={styles.methodSub}>Place custom landmark points on body photos</Text>
        </TouchableOpacity>

        {processingManual && (
          <View style={styles.manualLoading}>
            <ActivityIndicator size="small" color="#00D4AA" />
            <Text style={{ color: '#00D4AA', marginLeft: 8 }}>Computing manual measurements...</Text>
          </View>
        )}

        {/* Zoom Image Modal */}
        <ZoomableImageModal
          visible={Boolean(zoomImageUri)}
          imageSource={{ uri: zoomImageUri }}
          title={zoomTitle}
          onClose={() => setZoomImageUri(null)}
        />

        {/* Manual Landmark Modal */}
        <ManualLandmarkModal
          visible={manualModalVisible}
          imageUri={manualViewStep === 'front' ? capturedImages.front : capturedImages.side}
          imageType={manualViewStep}
          onComplete={handleManualLandmarkComplete}
          onCancel={() => setManualModalVisible(false)}
        />
      </ScrollView>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: '#000' }}>
      <Camera
        ref={cameraRef}
        style={StyleSheet.absoluteFill}
        device={device}
        isActive={true}
        photo={true}
        onInitialized={() => {
          console.log('[CameraScreen] VisionCamera preview initialized');
          setIsCameraReady(true);
        }}
        onError={(err) => {
          console.error('[CameraScreen] Camera error:', err);
        }}
      />

      {/* SVG Silhouette Overlay — Fix 1 & 3: Explicit hex stroke/fill */}
      <Svg
        width="100%"
        height="100%"
        viewBox="0 0 300 600"
        style={StyleSheet.absoluteFill}
        pointerEvents="none">
        {/* Head */}
        <Circle
          cx="150" cy="55" r="42"
          stroke={silhouetteColor}
          strokeWidth={3}
          fill={silhouetteFillColor}
          fillOpacity={silhouetteOpacity}
          strokeDasharray="8,4"
        />
        {/* Neck */}
        <Line x1="150" y1="97" x2="150" y2="125"
          stroke={silhouetteColor} strokeWidth={3}/>
        {/* Shoulders */}
        <Line x1="45" y1="140" x2="255" y2="140"
          stroke={silhouetteColor} strokeWidth={3}/>
        {/* Left arm A-pose */}
        <Line x1="45" y1="140" x2="10" y2="280"
          stroke={silhouetteColor} strokeWidth={3}/>
        {/* Right arm A-pose */}
        <Line x1="255" y1="140" x2="290" y2="280"
          stroke={silhouetteColor} strokeWidth={3}/>
        {/* Torso */}
        <Line x1="150" y1="125" x2="150" y2="350"
          stroke={silhouetteColor} strokeWidth={3}/>
        {/* Hips */}
        <Line x1="90" y1="350" x2="210" y2="350"
          stroke={silhouetteColor} strokeWidth={3}/>
        {/* Left leg */}
        <Line x1="108" y1="350" x2="92" y2="560"
          stroke={silhouetteColor} strokeWidth={3}/>
        {/* Right leg */}
        <Line x1="192" y1="350" x2="208" y2="560"
          stroke={silhouetteColor} strokeWidth={3}/>
      </Svg>

      {/* Status banner */}
      <View style={styles.statusBanner}>
        <Text style={[styles.statusText, { color: silhouetteColor }]}>
          {countdown !== null && countdown > 0
            ? `✅ Hold still! Capturing in ${countdown}...`
            : isAligned
            ? '✅ Aligned! Starting countdown...'
            : currentView === 'front'
            ? '👤 Stand facing camera in A-pose'
            : '↩️ Turn 90° to your right for side view'}
        </Text>
        <Text style={styles.viewSubtitle}>
          {currentView === 'front' ? 'VIEW 1 OF 2: FRONT VIEW' : 'VIEW 2 OF 2: SIDE VIEW'}
        </Text>
      </View>

      {/* Countdown Ring */}
      {countdown !== null && countdown > 0 && (
        <View style={[styles.countdownRing, { backgroundColor: '#00D4AA' }]}>
          <Text style={styles.countdownNumber}>{countdown}</Text>
        </View>
      )}

      {/* Front Thumbnail Preview while on Side View */}
      {capturedImages.front && currentView === 'side' && (
        <TouchableOpacity
          activeOpacity={0.8}
          onPress={() => { setZoomImageUri(capturedImages.front); setZoomTitle('Captured Front View Photo'); }}
          style={styles.thumbnailBadge}>
          <Image source={{ uri: capturedImages.front }} style={styles.thumbnailImg} />
          <Text style={styles.thumbnailLabel}>Front ✓</Text>
        </TouchableOpacity>
      )}

      {/* Zoom Image Modal */}
      <ZoomableImageModal
        visible={Boolean(zoomImageUri)}
        imageSource={{ uri: zoomImageUri }}
        title={zoomTitle}
        onClose={() => setZoomImageUri(null)}
      />

      {/* Fix 5 — Connection Status Badge */}
      <View style={styles.connectionStatus}>
        <View style={[styles.statusDot, { backgroundColor: isConnected ? '#00D4AA' : '#FFD700' }]} />
        <Text style={styles.connectionText}>
          {isConnected ? 'Live' : 'Offline mode'}
        </Text>
      </View>

      {/* Flip Camera Button */}
      <TouchableOpacity style={styles.flipBtn} onPress={flipCamera} activeOpacity={0.7}>
        <Text style={styles.flipBtnText}>🔄</Text>
      </TouchableOpacity>

      {/* Camera Mode Badge */}
      <View style={styles.cameraModeBadge}>
        <Text style={styles.cameraModeText}>
          {cameraPosition === 'front' ? '📷 Front Cam' : '📷 Rear Cam'}
        </Text>
      </View>

      {/* Back Button */}
      <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
        <Text style={styles.backBtnText}>←</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  connectionStatus: {
    position: 'absolute', top: 16, right: 16,
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.6)',
    borderRadius: 12, paddingHorizontal: 10, paddingVertical: 6,
    zIndex: 40,
  },
  statusDot: {
    width: 8, height: 8, borderRadius: 4, marginRight: 6,
  },
  connectionText: {
    color: '#fff', fontSize: 11, fontWeight: '600',
  },
  flipBtn: {
    position: 'absolute', top: 16, right: 105,
    backgroundColor: 'rgba(0,0,0,0.6)', borderRadius: 20,
    width: 38, height: 38, justifyContent: 'center', alignItems: 'center',
    zIndex: 40, borderWidth: 1.5, borderColor: '#00D4AA',
  },
  flipBtnText: { fontSize: 18 },
  cameraModeBadge: {
    position: 'absolute', top: 60, right: 16,
    backgroundColor: 'rgba(0,0,0,0.6)',
    borderRadius: 12, paddingHorizontal: 10, paddingVertical: 4,
    zIndex: 40, borderWidth: 1, borderColor: 'rgba(255,255,255,0.2)'
  },
  cameraModeText: {
    color: '#00D4AA', fontSize: 10, fontWeight: '700',
  },
  centerContainer: {
    flex: 1, backgroundColor: '#0A0E27',
    justifyContent: 'center', alignItems: 'center', padding: 20
  },
  infoText: { color: '#A0AEC0', fontSize: 16, textAlign: 'center' },
  backBtnInline: {
    marginTop: 20, paddingHorizontal: 20, paddingVertical: 10,
    backgroundColor: '#1A1F3A', borderRadius: 8
  },
  backBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  statusBanner: {
    position: 'absolute', top: 110, left: 16, right: 16,
    backgroundColor: 'rgba(0,0,0,0.7)', borderRadius: 20, padding: 10,
    alignItems: 'center', zIndex: 20
  },
  statusText: {
    fontSize: 15, fontWeight: '700', textAlign: 'center'
  },
  viewSubtitle: {
    color: '#A0AEC0', fontSize: 12, fontWeight: '600', marginTop: 6,
    textTransform: 'uppercase', letterSpacing: 1
  },
  countdownRing: {
    position: 'absolute', alignSelf: 'center', top: '40%',
    width: 110, height: 110, borderRadius: 55,
    justifyContent: 'center', alignItems: 'center',
    borderWidth: 4, borderColor: '#FFFFFF',
    zIndex: 30, shadowColor: '#000', shadowOpacity: 0.4, shadowRadius: 10
  },
  countdownNumber: {
    color: '#FFFFFF', fontSize: 60, fontWeight: '900'
  },
  thumbnailBadge: {
    position: 'absolute', bottom: 40, right: 20,
    borderWidth: 2, borderColor: '#00D4AA', borderRadius: 10,
    backgroundColor: 'rgba(0,0,0,0.6)', padding: 4, zIndex: 20
  },
  thumbnailImg: { width: 64, height: 86, borderRadius: 6 },
  thumbnailLabel: { color: '#00D4AA', fontSize: 10, fontWeight: '700', textAlign: 'center', marginTop: 2 },
  backBtn: {
    position: 'absolute', top: 16, left: 16,
    backgroundColor: 'rgba(0,0,0,0.6)', borderRadius: 20,
    width: 40, height: 40, justifyContent: 'center', alignItems: 'center',
    zIndex: 40
  },
  reviewContainer: { flex: 1, backgroundColor: '#0A0E27' },
  reviewContent: { padding: 20, paddingTop: 60, paddingBottom: 40 },
  reviewHeader: { color: '#fff', fontSize: 24, fontWeight: '800', textAlign: 'center' },
  reviewSubheader: { color: '#A0AEC0', fontSize: 14, textAlign: 'center', marginTop: 4, marginBottom: 24 },
  reviewGrid: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 24 },
  reviewCard: { width: '48%', backgroundColor: '#1A1F3A', borderRadius: 12, padding: 10, alignItems: 'center' },
  cardLabel: { color: '#00D4AA', fontSize: 14, fontWeight: '700', marginBottom: 8 },
  cardImage: { width: '100%', height: 180, borderRadius: 8, resizeMode: 'cover' },
  missingImage: { width: '100%', height: 180, borderRadius: 8, backgroundColor: '#2D3748', justifyContent: 'center', alignItems: 'center' },
  missingText: { color: '#A0AEC0', fontSize: 12 },
  retakeBtn: { marginTop: 10, paddingVertical: 6, paddingHorizontal: 12, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 6 },
  retakeBtnText: { color: '#fff', fontSize: 12, fontWeight: '600' },
  heightBox: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#1A1F3A', padding: 14, borderRadius: 12, marginBottom: 24 },
  heightLabel: { color: '#fff', fontSize: 16, fontWeight: '600', marginRight: 12 },
  heightInput: { backgroundColor: '#2D3748', color: '#fff', fontSize: 16, fontWeight: '700', paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8, width: 80, textAlign: 'center' },
  methodHeader: { color: '#fff', fontSize: 18, fontWeight: '700', marginBottom: 16 },
  methodBtnAi: { backgroundColor: '#00D4AA', padding: 16, borderRadius: 12, marginBottom: 14 },
  methodBtnManual: { backgroundColor: '#1A1F3A', padding: 16, borderRadius: 12, borderWidth: 1, borderColor: '#4A5568', marginBottom: 14 },
  methodTitle: { color: '#fff', fontSize: 16, fontWeight: '800' },
  methodSub: { color: 'rgba(255,255,255,0.8)', fontSize: 12, marginTop: 4 },
  manualLoading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 12 }
});

export default CameraScreen;
