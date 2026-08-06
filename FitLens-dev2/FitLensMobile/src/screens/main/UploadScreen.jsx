import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import axios from 'axios';
import Header from '../../components/common/Header';
import Button from '../../components/common/Button';
import PhotoUploadCard from '../../components/upload/PhotoUploadCard';
import HeightSelector from '../../components/upload/HeightSelector';
import ErrorMessage from '../../components/common/ErrorMessage';
import { cameraService } from '../../services/cameraService';
import axiosInstance from '../../api/axiosInstance';
import { Config } from '../../constants/config';
import { Colors } from '../../constants/colors';
import useAuthStore from '../../store/authStore';

const UploadScreen = ({ navigation }) => {
  const [frontPhoto, setFrontPhoto] = useState(null);
  const [sidePhoto, setSidePhoto] = useState(null);
  const [userHeight, setUserHeight] = useState('165');
  const [validating, setValidating] = useState(false);
  const logout = useAuthStore((state) => state.logout);

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
      // Show specific error for multiple persons:
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

  const handleProcess = async () => {
    if (!frontPhoto?.uri) {
      Alert.alert('Required', 'Please select a Front View photo');
      return;
    }
    if (!sidePhoto?.uri) {
      Alert.alert('Required', 'Please select a Side View photo');
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

        <Button
          title={'⚡ Analyze & Calculate Measurements'}
          onPress={handleProcess}
          disabled={!frontPhoto || !sidePhoto || validating}
          style={{ marginTop: 12 }}
        />
      </ScrollView>
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
});

export default UploadScreen;
