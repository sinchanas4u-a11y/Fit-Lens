import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert, ActivityIndicator, TouchableOpacity } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import axios from 'axios';
import Header from '../../components/common/Header';
import Button from '../../components/common/Button';
import PhotoUploadCard from '../../components/upload/PhotoUploadCard';
import HeightSelector from '../../components/upload/HeightSelector';
import ManualLandmarkModal from '../../components/measurement/ManualLandmarkModal';
import { cameraService } from '../../services/cameraService';
import { Config } from '../../constants/config';
import { Colors } from '../../constants/colors';
import { useAuthStore } from '../../store/authStore';
import { uriToBase64 } from '../../utils/base64Utils';
import { measurementApi } from '../../api/measurementApi';

const UploadScreen = ({ navigation }) => {
  const [frontPhoto, setFrontPhoto] = useState(null);
  const [sidePhoto, setSidePhoto] = useState(null);
  const [userHeight, setUserHeight] = useState('165');
  const [validating, setValidating] = useState(false);
  const [processingManual, setProcessingManual] = useState(false);

  // Manual Landmark Marking States
  const [manualModalVisible, setManualModalVisible] = useState(false);
  const [manualViewStep, setManualViewStep] = useState('front'); // 'front' or 'side'
  const [manualLandmarks, setManualLandmarks] = useState({ front: null, side: null });

  const validatePhoto = async (imageUri, view) => {
    try {
      setValidating(true);
      const formData = new FormData();
      formData.append('image', {
        uri: imageUri,
        type: 'image/jpeg',
        name: `${view}.jpg`,
      });
      formData.append('view', view);

      const res = await axios.post(
        `${Config.BASE_URL}/validate/person-count`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 10000 }
      );

      if (!res.data.success) {
        Alert.alert('Validation Failed', res.data.error || 'Person detection failed. Please retake photo.');
        return false;
      }
      return true;
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message || 'Validation error';
      if (errorMsg.includes('Multiple') || errorMsg.includes('multiple')) {
        Alert.alert(
          '⚠️ Multiple Persons Detected',
          'Only one person should be in the frame. Please retake with only yourself visible.',
          [{ text: 'Retake', style: 'destructive' }]
        );
      } else {
        Alert.alert('Validation Error', errorMsg);
      }
      return false;
    } finally {
      setValidating(false);
    }
  };

  const handleSelectPhoto = async (view) => {
    Alert.alert('Select Source', `Upload ${view.toUpperCase()} View Photo`, [
      {
        text: '📷 Camera',
        onPress: async () => {
          const res = await cameraService.openCamera();
          if (res?.uri) {
            const valid = await validatePhoto(res.uri, view);
            if (valid) {
              if (view === 'front') setFrontPhoto(res);
              else setSidePhoto(res);
            }
          }
        },
      },
      {
        text: '🖼️ Gallery',
        onPress: async () => {
          const res = await cameraService.openGallery();
          if (res?.uri) {
            const valid = await validatePhoto(res.uri, view);
            if (valid) {
              if (view === 'front') setFrontPhoto(res);
              else setSidePhoto(res);
            }
          }
        },
      },
      { text: 'Cancel', style: 'cancel' },
    ]);
  };

  const handleProcessAuto = () => {
    if (!frontPhoto?.uri || !sidePhoto?.uri) {
      Alert.alert('Required', 'Please upload both Front and Side view photos');
      return;
    }
    if (!userHeight || isNaN(parseFloat(userHeight))) {
      Alert.alert('Required', 'Please enter a valid height in cm');
      return;
    }

    navigation.navigate('Processing', {
      frontImageUri: frontPhoto.uri,
      sideImageUri: sidePhoto.uri,
      userHeightCm: parseFloat(userHeight) || 165,
    });
  };

  const handleStartManualMarking = () => {
    if (!frontPhoto?.uri) {
      Alert.alert('Required', 'Please upload Front View photo first');
      return;
    }
    if (!userHeight || isNaN(parseFloat(userHeight))) {
      Alert.alert('Required', 'Please enter a valid height in cm');
      return;
    }

    setManualLandmarks({ front: null, side: null });
    setManualViewStep('front');
    setManualModalVisible(true);
  };

  const handleManualLandmarkComplete = async (viewData) => {
    setManualModalVisible(false);

    if (manualViewStep === 'front') {
      const updatedLandmarks = { ...manualLandmarks, front: viewData };
      setManualLandmarks(updatedLandmarks);

      if (sidePhoto?.uri) {
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

      const frontB64 = frontPhoto?.uri ? await uriToBase64(frontPhoto.uri) : null;
      const sideB64 = sidePhoto?.uri ? await uriToBase64(sidePhoto.uri) : null;

      const requestPayload = {
        user_height: parseFloat(userHeight) || 165,
        front_landmarks: finalLandmarks.front || null,
        side_landmarks: finalLandmarks.side || null,
        front_image: frontB64,
        side_image: sideB64,
      };

      const res = await measurementApi.processManual(requestPayload);

      if (res.data?.success) {
        navigation.navigate('Results', { data: res.data });
      } else {
        Alert.alert('Manual Processing Failed', res.data?.error || 'Could not compute measurements.');
      }
    } catch (err) {
      console.error('Manual processing error:', err);
      Alert.alert('Processing Failed', err.response?.data?.error || err.message || 'Error processing manual landmarks.');
    } finally {
      setProcessingManual(false);
    }
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <Header title="Upload Photos" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.content}>
        {validating && (
          <View style={styles.validatingBox}>
            <ActivityIndicator color={Colors.accent} size="small" />
            <Text style={styles.validatingText}>Validating person detection...</Text>
          </View>
        )}

        {processingManual && (
          <View style={styles.validatingBox}>
            <ActivityIndicator color="#00D4AA" size="small" />
            <Text style={[styles.validatingText, { color: '#00D4AA' }]}>Processing manual landmarks...</Text>
          </View>
        )}

        <HeightSelector heightCm={userHeight} onChangeHeightCm={setUserHeight} />

        <PhotoUploadCard
          title="Front View Photo *"
          description="Stand facing camera in A-pose"
          imageUri={frontPhoto?.uri}
          onSelect={() => handleSelectPhoto('front')}
          onRemove={() => setFrontPhoto(null)}
        />

        <PhotoUploadCard
          title="Side View Photo *"
          description="Turn 90° to the side"
          imageUri={sidePhoto?.uri}
          onSelect={() => handleSelectPhoto('side')}
          onRemove={() => setSidePhoto(null)}
        />

        {/* Mode Buttons */}
        <Button
          title={'⚡ Automatic AI Detection'}
          onPress={handleProcessAuto}
          disabled={!frontPhoto || !sidePhoto || validating || processingManual}
          style={{ marginTop: 16 }}
        />

        <TouchableOpacity
          onPress={handleStartManualMarking}
          disabled={!frontPhoto || validating || processingManual}
          style={[
            styles.manualBtn,
            (!frontPhoto || validating || processingManual) && { opacity: 0.5 },
          ]}>
          <Text style={styles.manualBtnText}>✋ Manual Landmark Marking</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Manual Landmark Modal */}
      <ManualLandmarkModal
        visible={manualModalVisible}
        imageUri={manualViewStep === 'front' ? frontPhoto?.uri : sidePhoto?.uri}
        imageType={manualViewStep}
        onComplete={handleManualLandmarkComplete}
        onCancel={() => setManualModalVisible(false)}
      />
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 20, paddingBottom: 40 },
  validatingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.cardBg,
    padding: 12,
    borderRadius: 10,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.accent,
  },
  validatingText: { color: Colors.accent, marginLeft: 10, fontSize: 13, fontWeight: '600' },
  manualBtn: {
    backgroundColor: Colors.cardBg,
    padding: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginTop: 12,
    borderWidth: 1.5,
    borderColor: '#9B59B6',
  },
  manualBtnText: { color: '#9B59B6', fontSize: 15, fontWeight: '700' },
});

export default UploadScreen;
