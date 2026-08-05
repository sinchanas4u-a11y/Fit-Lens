import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, Alert } from 'react-native';
import { cameraService } from '../../services/cameraService';
import SilhouetteOverlay from '../../components/camera/SilhouetteOverlay';
import CountdownOverlay from '../../components/camera/CountdownOverlay';
import CapturedThumbnail from '../../components/camera/CapturedThumbnail';
import HeightSelector from '../../components/upload/HeightSelector';
import Button from '../../components/common/Button';
import { Colors } from '../../constants/colors';

const CameraScreen = ({ navigation }) => {
  const [viewMode, setViewMode] = useState('front'); // 'front' or 'side'
  const [frontPhoto, setFrontPhoto] = useState(null);
  const [sidePhoto, setSidePhoto] = useState(null);
  const [userHeight, setUserHeight] = useState('165');
  const [countdown, setCountdown] = useState(0);

  const startAutoCapture = () => {
    setCountdown(3);
  };

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setTimeout(() => {
      if (countdown === 1) {
        setCountdown(0);
        triggerCapture();
      } else {
        setCountdown(countdown - 1);
      }
    }, 1000);
    return () => clearTimeout(timer);
  }, [countdown]);

  const triggerCapture = async () => {
    const photo = await cameraService.openCamera();
    if (!photo) return;

    if (viewMode === 'front') {
      setFrontPhoto(photo);
      setViewMode('side');
      Alert.alert('Front View Captured!', 'Now turn 90° to capture Side View.');
    } else {
      setSidePhoto(photo);
    }
  };

  const handleProcess = () => {
    if (!frontPhoto?.base64 || !sidePhoto?.base64) {
      Alert.alert('Missing Views', 'Please capture both Front and Side view photos');
      return;
    }
    navigation.navigate('Processing', {
      frontB64: frontPhoto.base64,
      sideB64: sidePhoto.base64,
      heightCm: userHeight,
    });
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>
          {viewMode === 'front' ? '1. Capture Front View' : '2. Capture Side View'}
        </Text>
        <View style={{ width: 32 }} />
      </View>

      {/* Camera Viewport Placeholder / Silhouette Overlay */}
      <View style={styles.cameraBox}>
        <SilhouetteOverlay viewMode={viewMode} />
        <CountdownOverlay seconds={countdown} />
      </View>

      {/* Controls & Thumbnails */}
      <View style={styles.controlsWrap}>
        <View style={styles.thumbsRow}>
          <CapturedThumbnail
            label="Front View"
            imageUri={frontPhoto?.uri}
            onRetake={() => { setFrontPhoto(null); setViewMode('front'); }}
          />
          <CapturedThumbnail
            label="Side View"
            imageUri={sidePhoto?.uri}
            onRetake={() => { setSidePhoto(null); setViewMode('side'); }}
          />
        </View>

        <HeightSelector heightCm={userHeight} onChangeHeightCm={setUserHeight} />

        {frontPhoto && sidePhoto ? (
          <Button
            title="⚡ Analyze Photos Now"
            onPress={handleProcess}
          />
        ) : (
          <TouchableOpacity style={styles.captureBtn} onPress={startAutoCapture}>
            <View style={styles.captureInner} />
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.primary },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    paddingTop: 48,
    backgroundColor: Colors.secondary,
  },
  backText: { color: Colors.textPrimary, fontSize: 24 },
  headerTitle: { color: Colors.textPrimary, fontSize: 16, fontWeight: '700' },
  cameraBox: { flex: 1, backgroundColor: '#000', position: 'relative' },
  controlsWrap: {
    padding: 20,
    backgroundColor: Colors.secondary,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  thumbsRow: { flexDirection: 'row', gap: 12, justifyContent: 'center', marginBottom: 12 },
  captureBtn: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 4,
    borderColor: Colors.accent,
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'center',
    marginTop: 4,
  },
  captureInner: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: Colors.accent,
  },
});

export default CameraScreen;
