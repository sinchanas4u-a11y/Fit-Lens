import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, Alert } from 'react-native';
import { Camera, useCameraDevice } from 'react-native-vision-camera';
import Svg, { Circle, Line } from 'react-native-svg';
import axios from 'axios';
import { Config } from '../../constants/config';

const CameraScreen = ({ navigation }) => {
  const [isAligned, setIsAligned] = useState(false);
  const [countdown, setCountdown] = useState(3);
  const [captureStep, setCaptureStep] = useState(1); // 1=front, 2=side
  const [frontCapture, setFrontCapture] = useState(null);
  const [checking, setChecking] = useState(false);
  const [userHeight, setUserHeight] = useState('165');
  
  const cameraRef = useRef(null);
  const countdownTimer = useRef(null);
  const alignmentInterval = useRef(null);
  
  const device = useCameraDevice('back') || useCameraDevice('front');

  // Check alignment every 2 seconds by capturing and validating:
  useEffect(() => {
    startAlignmentCheck();
    return () => {
      clearInterval(alignmentInterval.current);
      clearTimeout(countdownTimer.current);
    };
  }, [captureStep]);

  const startAlignmentCheck = () => {
    clearInterval(alignmentInterval.current);
    alignmentInterval.current = setInterval(async () => {
      if (checking || !cameraRef.current) return;
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
        if (aligned) startCountdown();
        else resetCountdown();
      } catch {
        setIsAligned(false);
        resetCountdown();
      }
      setChecking(false);
    }, 2000);
  };

  let countdownVal = 3;
  const startCountdown = () => {
    if (countdownTimer.current) return; // Already counting
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

  const capturePhoto = async () => {
    clearInterval(alignmentInterval.current);
    try {
      let uri = null;
      if (cameraRef.current) {
        const photo = await cameraRef.current.takePhoto({ quality: 1 });
        uri = `file://${photo.path}`;
      } else {
        uri = frontCapture || 'mock_photo_uri';
      }

      if (captureStep === 1) {
        setFrontCapture(uri);
        setCaptureStep(2);
        setIsAligned(false);
        setCountdown(3);
        // Show instruction to turn sideways
        Alert.alert(
          '✅ Front view captured!',
          'Now turn 90° to your right for the side view.',
          [{ text: 'Ready', onPress: () => startAlignmentCheck() }]
        );
      } else {
        // Both captured — navigate to processing
        navigation.replace('Processing', {
          frontImageUri: frontCapture,
          sideImageUri: uri,
          userHeightCm: parseFloat(userHeight) || 165,
        });
      }
    } catch (e) {
      Alert.alert('Capture Error', e.message);
    }
  };

  // Silhouette color: green if aligned, red if not:
  const silhouetteColor = isAligned ? '#00D4AA' : '#FC4444';

  const SilhouetteSvg = () => (
    <Svg width="200" height="380"
      style={{ position: 'absolute', alignSelf: 'center', top: '5%' }}>
      {/* Head */}
      <Circle cx="100" cy="40" r="30"
        stroke={silhouetteColor} strokeWidth="3"
        fill={silhouetteColor + '20'} strokeDasharray="6,3"/>
      {/* Neck */}
      <Line x1="100" y1="70" x2="100" y2="95"
        stroke={silhouetteColor} strokeWidth="3"/>
      {/* Shoulders */}
      <Line x1="30" y1="105" x2="170" y2="105"
        stroke={silhouetteColor} strokeWidth="3"/>
      {/* Left arm — A-pose */}
      <Line x1="30" y1="105" x2="5" y2="200"
        stroke={silhouetteColor} strokeWidth="3"/>
      {/* Right arm — A-pose */}
      <Line x1="170" y1="105" x2="195" y2="200"
        stroke={silhouetteColor} strokeWidth="3"/>
      {/* Torso */}
      <Line x1="100" y1="95" x2="100" y2="230"
        stroke={silhouetteColor} strokeWidth="3"/>
      {/* Hips */}
      <Line x1="55" y1="230" x2="145" y2="230"
        stroke={silhouetteColor} strokeWidth="3"/>
      {/* Left leg */}
      <Line x1="68" y1="230" x2="58" y2="370"
        stroke={silhouetteColor} strokeWidth="3"/>
      {/* Right leg */}
      <Line x1="132" y1="230" x2="142" y2="370"
        stroke={silhouetteColor} strokeWidth="3"/>
    </Svg>
  );

  return (
    <View style={{ flex: 1, backgroundColor: '#000' }}>
      {/* Camera */}
      {device ? (
        <Camera
          ref={cameraRef}
          style={StyleSheet.absoluteFill}
          device={device}
          isActive
          photo
        />
      ) : (
        <View style={[StyleSheet.absoluteFill, { backgroundColor: '#1A1F3A', justifyContent: 'center', alignItems: 'center' }]}>
          <Text style={{ color: '#A0AEC0' }}>Camera Preview Active</Text>
        </View>
      )}

      {/* Silhouette overlay */}
      <SilhouetteSvg />

      {/* Alignment status message */}
      <View style={styles.alignMsg}>
        <Text style={[styles.alignText, { color: silhouetteColor }]}>
          {isAligned
            ? `✅ Aligned! Capturing in ${countdown}...`
            : `${captureStep === 1 ? '📷 Front View' : '📷 Side View'} — Align body with silhouette`}
        </Text>
      </View>

      {/* Countdown circle when aligned */}
      {isAligned && (
        <View style={styles.countdownCircle}>
          <Text style={styles.countdownText}>{countdown}</Text>
        </View>
      )}

      {/* Front thumbnail after capture */}
      {frontCapture && captureStep === 2 && (
        <View style={styles.thumbnail}>
          <Image source={{ uri: frontCapture }}
            style={styles.thumbnailImg} />
          <Text style={styles.thumbnailLabel}>Front ✓</Text>
        </View>
      )}

      {/* Manual capture button */}
      <TouchableOpacity style={styles.captureBtn}
        onPress={capturePhoto}>
        <View style={[styles.captureBtnInner,
          { backgroundColor: silhouetteColor }]} />
      </TouchableOpacity>

      {/* Step + height info */}
      <View style={styles.bottomInfo}>
        <Text style={styles.stepText}>
          Step {captureStep} of 2: {captureStep === 1 ? 'Front View' : 'Side View'}
        </Text>
      </View>

      {/* Back button */}
      <TouchableOpacity style={styles.backBtn}
        onPress={() => navigation.goBack()}>
        <Text style={styles.backBtnText}>←</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  alignMsg: {
    position: 'absolute', top: 60, left: 0, right: 0,
    alignItems: 'center'
  },
  alignText: { fontSize: 16, fontWeight: '700',
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20 },
  countdownCircle: {
    position: 'absolute', alignSelf: 'center', top: '40%',
    width: 100, height: 100, borderRadius: 50,
    backgroundColor: '#00D4AA', justifyContent: 'center', alignItems: 'center'
  },
  countdownText: { color: '#fff', fontSize: 48, fontWeight: '900' },
  captureBtn: {
    position: 'absolute', bottom: 60, alignSelf: 'center',
    width: 80, height: 80, borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.3)',
    justifyContent: 'center', alignItems: 'center',
    borderWidth: 3, borderColor: '#fff'
  },
  captureBtnInner: { width: 64, height: 64, borderRadius: 32 },
  thumbnail: {
    position: 'absolute', bottom: 100, right: 16,
    borderWidth: 2, borderColor: '#00D4AA', borderRadius: 8
  },
  thumbnailImg: { width: 70, height: 90, borderRadius: 6 },
  thumbnailLabel: { color: '#00D4AA', textAlign: 'center',
    fontSize: 10, fontWeight: '700', padding: 2 },
  bottomInfo: {
    position: 'absolute', bottom: 16, left: 0, right: 0, alignItems: 'center'
  },
  stepText: { color: 'rgba(255,255,255,0.8)', fontSize: 13 },
  backBtn: {
    position: 'absolute', top: 52, left: 16,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 20, padding: 8
  },
  backBtnText: { color: '#fff', fontSize: 20 },
});

export default CameraScreen;
