import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, Alert, ActivityIndicator } from 'react-native';
import { Camera, useCameraDevice } from 'react-native-vision-camera';
import Svg, { Circle, Line } from 'react-native-svg';
import axios from 'axios';
import { Config } from '../../constants/config';
import ManualLandmarkModal from '../../components/measurement/ManualLandmarkModal';
import { uriToBase64 } from '../../utils/base64Utils';
import { measurementApi } from '../../api/measurementApi';

const CameraScreen = ({ navigation }) => {
  const [hasPermission, setHasPermission] = useState(false);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [isAligned, setIsAligned] = useState(false);
  const [personDetected, setPersonDetected] = useState(false);
  const [countdown, setCountdown] = useState(3);
  const [captureStep, setCaptureStep] = useState(1); // 1=front, 2=side
  const [frontCapture, setFrontCapture] = useState(null);
  const [sideCapture, setSideCapture] = useState(null);
  const [checking, setChecking] = useState(false);
  const [userHeight, setUserHeight] = useState('165');
  const [processingManual, setProcessingManual] = useState(false);

  // Manual Marking States
  const [manualModalVisible, setManualModalVisible] = useState(false);
  const [manualViewStep, setManualViewStep] = useState('front');
  const [manualLandmarks, setManualLandmarks] = useState({ front: null, side: null });
  
  const cameraRef = useRef(null);
  const countdownTimer = useRef(null);
  const alignmentInterval = useRef(null);
  
  const backDevice = useCameraDevice('back');
  const frontDevice = useCameraDevice('front');
  const device = backDevice || frontDevice;

  useEffect(() => {
    (async () => {
      try {
        const permission = await Camera.requestCameraPermission();
        setHasPermission(permission === 'granted');
        if (permission !== 'granted') {
          Alert.alert(
            'Camera Permission Required',
            'FitLens needs camera access to capture body measurements.',
            [{ text: 'Go Back', onPress: () => navigation.goBack() }]
          );
        }
      } catch (err) {
        console.error('Failed to request camera permission:', err);
      }
    })();
  }, []);

  useEffect(() => {
    if (isCameraReady && hasPermission && device) {
      startAlignmentCheck();
    }
    return () => {
      clearInterval(alignmentInterval.current);
      clearTimeout(countdownTimer.current);
    };
  }, [captureStep, isCameraReady, hasPermission, device]);

  const startAlignmentCheck = () => {
    clearInterval(alignmentInterval.current);
    alignmentInterval.current = setInterval(async () => {
      if (checking || !cameraRef.current || !isCameraReady) return;
      setChecking(true);
      try {
        const photo = await cameraRef.current.takePhoto({ quality: 0.5 });
        const formData = new FormData();
        formData.append('image', {
          uri: `file://${photo.path}`,
          type: 'image/jpeg', name: 'frame.jpg'
        });
        formData.append('view', captureStep === 1 ? 'front' : 'side');
        const res = await axios.post(
          `${Config.BASE_URL}/validate/person-count`,
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 5000 }
        );
        const aligned = res.data.success === true;
        setIsAligned(aligned);
        setPersonDetected(aligned);

        if (aligned) startCountdown();
        else resetCountdown();
      } catch {
        setIsAligned(false);
        setPersonDetected(false);
        resetCountdown();
      }
      setChecking(false);
    }, 2000);
  };

  let countdownVal = 3;
  const startCountdown = () => {
    if (countdownTimer.current) return;
    countdownTimer.current = setInterval(() => {
      countdownVal--;
      setCountdown(countdownVal);
      if (countdownVal <= 0) {
        clearInterval(countdownTimer.current);
        countdownTimer.current = null;
        capturePhoto();
      }
    }, 1000);
  };

  const resetCountdown = () => {
    clearInterval(countdownTimer.current);
    countdownTimer.current = null;
    countdownVal = 3;
    setCountdown(3);
  };

  const handleCapturePress = () => {
    if (!isCameraReady) {
      Alert.alert('Camera Not Ready', 'Please wait for camera preview to initialize.');
      return;
    }
    if (!personDetected || !isAligned) {
      Alert.alert(
        '⚠️ No Person Detected',
        'No person detected in frame. Please align your body with the silhouette before capturing.',
        [{ text: 'OK' }]
      );
      return;
    }
    capturePhoto();
  };

  const capturePhoto = async () => {
    if (!isCameraReady || !cameraRef.current) {
      Alert.alert('Camera Not Ready', 'Please wait for camera preview to initialize.');
      return;
    }
    clearInterval(alignmentInterval.current);
    try {
      const photo = await cameraRef.current.takePhoto({ quality: 1 });
      const uri = `file://${photo.path}`;

      if (captureStep === 1) {
        setFrontCapture(uri);
        setCaptureStep(2);
        setIsAligned(false);
        setPersonDetected(false);
        setCountdown(3);
        Alert.alert(
          '✅ Front view captured!',
          'Now turn 90° to your right for the side view.',
          [{ text: 'Ready', onPress: () => startAlignmentCheck() }]
        );
      } else {
        // Both captured
        setSideCapture(uri);
        Alert.alert(
          '✅ Both Views Captured!',
          'Select how you would like to compute your measurements:',
          [
            {
              text: '⚡ Automatic AI Mode',
              onPress: () => {
                navigation.replace('Processing', {
                  frontImageUri: frontCapture,
                  sideImageUri: uri,
                  userHeightCm: parseFloat(userHeight) || 165,
                });
              },
            },
            {
              text: '✋ Manual Landmark Marking',
              onPress: () => {
                setManualLandmarks({ front: null, side: null });
                setManualViewStep('front');
                setManualModalVisible(true);
              },
            },
          ]
        );
      }
    } catch (e) {
      Alert.alert('Capture Error', e.message);
    }
  };

  const handleManualLandmarkComplete = async (viewData) => {
    setManualModalVisible(false);

    if (manualViewStep === 'front') {
      const updatedLandmarks = { ...manualLandmarks, front: viewData };
      setManualLandmarks(updatedLandmarks);

      if (sideCapture) {
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
      console.log('🎯 Submitting camera manual landmarks to backend...');

      const frontB64 = frontCapture ? await uriToBase64(frontCapture) : null;
      const sideB64 = sideCapture ? await uriToBase64(sideCapture) : null;

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

  const silhouetteColor = (isAligned && personDetected) ? '#00D4AA' : '#FC4444';
  const canCapture = isCameraReady && isAligned && personDetected;

  const SilhouetteSvg = () => (
    <Svg width="200" height="380"
      style={{ position: 'absolute', alignSelf: 'center', top: '5%' }}>
      <Circle cx="100" cy="40" r="30"
        stroke={silhouetteColor} strokeWidth="3"
        fill={silhouetteColor + '20'} strokeDasharray="6,3"/>
      <Line x1="100" y1="70" x2="100" y2="95"
        stroke={silhouetteColor} strokeWidth="3"/>
      <Line x1="30" y1="105" x2="170" y2="105"
        stroke={silhouetteColor} strokeWidth="3"/>
      <Line x1="30" y1="105" x2="5" y2="200"
        stroke={silhouetteColor} strokeWidth="3"/>
      <Line x1="170" y1="105" x2="195" y2="200"
        stroke={silhouetteColor} strokeWidth="3"/>
      <Line x1="100" y1="95" x2="100" y2="230"
        stroke={silhouetteColor} strokeWidth="3"/>
      <Line x1="55" y1="230" x2="145" y2="230"
        stroke={silhouetteColor} strokeWidth="3"/>
      <Line x1="68" y1="230" x2="58" y2="370"
        stroke={silhouetteColor} strokeWidth="3"/>
      <Line x1="132" y1="230" x2="142" y2="370"
        stroke={silhouetteColor} strokeWidth="3"/>
    </Svg>
  );

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

  return (
    <View style={{ flex: 1, backgroundColor: '#000' }}>
      <Camera
        ref={cameraRef}
        style={StyleSheet.absoluteFill}
        device={device}
        isActive={true}
        photo={true}
        onInitialized={() => {
          console.log('[CameraScreen] VisionCamera initialized');
          setIsCameraReady(true);
        }}
        onError={(err) => {
          console.error('[CameraScreen] Camera error:', err);
        }}
      />

      {(!isCameraReady || processingManual) && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#00D4AA" />
          <Text style={{ color: '#fff', marginTop: 10 }}>
            {processingManual ? 'Processing manual landmarks...' : 'Starting camera...'}
          </Text>
        </View>
      )}

      <SilhouetteSvg />

      <View style={styles.alignMsg}>
        <Text style={[styles.alignText, { color: silhouetteColor }]}>
          {!isCameraReady
            ? '📷 Starting Camera...'
            : isAligned && personDetected
            ? `✅ Person Detected! Capturing in ${countdown}...`
            : `⚠️ No person detected — align body with silhouette`}
        </Text>
      </View>

      {isAligned && personDetected && isCameraReady && (
        <View style={styles.countdownCircle}>
          <Text style={styles.countdownText}>{countdown}</Text>
        </View>
      )}

      {frontCapture && captureStep === 2 && (
        <View style={styles.thumbnail}>
          <Image source={{ uri: frontCapture }}
            style={styles.thumbnailImg} />
          <Text style={styles.thumbnailLabel}>Front ✓</Text>
        </View>
      )}

      <TouchableOpacity
        style={[
          styles.captureBtn,
          !canCapture && { opacity: 0.4, borderColor: '#718096' }
        ]}
        onPress={handleCapturePress}>
        <View style={[styles.captureBtnInner, { backgroundColor: canCapture ? '#00D4AA' : '#718096' }]} />
      </TouchableOpacity>

      <View style={styles.bottomInfo}>
        <Text style={styles.stepText}>
          Step {captureStep} of 2: {captureStep === 1 ? 'Front View' : 'Side View'}
        </Text>
      </View>

      <TouchableOpacity style={styles.backBtn}
        onPress={() => navigation.goBack()}>
        <Text style={styles.backBtnText}>←</Text>
      </TouchableOpacity>

      {/* Manual Landmark Modal */}
      <ManualLandmarkModal
        visible={manualModalVisible}
        imageUri={manualViewStep === 'front' ? frontCapture : sideCapture}
        imageType={manualViewStep}
        onComplete={handleManualLandmarkComplete}
        onCancel={() => setManualModalVisible(false)}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  centerContainer: {
    flex: 1, backgroundColor: '#0A0E27',
    justifyContent: 'center', alignItems: 'center', padding: 20
  },
  infoText: { color: '#A0AEC0', fontSize: 16, textAlign: 'center' },
  backBtnInline: {
    marginTop: 20, paddingHorizontal: 20, paddingVertical: 10,
    backgroundColor: '#1A1F3A', borderRadius: 8
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(10,14,39,0.85)',
    justifyContent: 'center', alignItems: 'center', zIndex: 10
  },
  alignMsg: {
    position: 'absolute', top: 60, left: 0, right: 0,
    alignItems: 'center', zIndex: 20
  },
  alignText: { fontSize: 15, fontWeight: '700',
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20 },
  countdownCircle: {
    position: 'absolute', alignSelf: 'center', top: '40%',
    width: 100, height: 100, borderRadius: 50,
    backgroundColor: '#00D4AA', justifyContent: 'center', alignItems: 'center', zIndex: 20
  },
  countdownText: { color: '#fff', fontSize: 48, fontWeight: '900' },
  captureBtn: {
    position: 'absolute', bottom: 60, alignSelf: 'center',
    width: 80, height: 80, borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.3)',
    justifyContent: 'center', alignItems: 'center',
    borderWidth: 3, borderColor: '#fff', zIndex: 20
  },
  captureBtnInner: { width: 64, height: 64, borderRadius: 32 },
  thumbnail: {
    position: 'absolute', bottom: 100, right: 16,
    borderWidth: 2, borderColor: '#00D4AA', borderRadius: 8, zIndex: 20
  },
  thumbnailImg: { width: 70, height: 90, borderRadius: 6 },
  thumbnailLabel: { color: '#00D4AA', textAlign: 'center',
    fontSize: 10, fontWeight: '700', padding: 2 },
  bottomInfo: {
    position: 'absolute', bottom: 16, left: 0, right: 0, alignItems: 'center', zIndex: 20
  },
  stepText: { color: 'rgba(255,255,255,0.8)', fontSize: 13 },
  backBtn: {
    position: 'absolute', top: 52, left: 16,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 20, padding: 8, zIndex: 20
  },
  backBtnText: { color: '#fff', fontSize: 20 },
});

export default CameraScreen;
