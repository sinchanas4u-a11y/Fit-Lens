import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Header from '../../components/common/Header';
import Button from '../../components/common/Button';
import PhotoUploadCard from '../../components/upload/PhotoUploadCard';
import HeightSelector from '../../components/upload/HeightSelector';
import ErrorMessage from '../../components/common/ErrorMessage';
import { cameraService } from '../../services/cameraService';
import { uploadApi } from '../../api/uploadApi';
import { Colors } from '../../constants/colors';
import { useUpload } from '../../hooks/useUpload';

const UploadScreen = ({ navigation }) => {
  const [frontPhoto, setFrontPhoto] = useState(null);
  const [sidePhoto, setSidePhoto] = useState(null);
  const [userHeight, setUserHeight] = useState('165');
  const [validatingFront, setValidatingFront] = useState(false);
  const [validatingSide, setValidatingSide] = useState(false);
  const { processUpload, loading, error } = useUpload();

  const handleSelectPhoto = async (view) => {
    Alert.alert('Select Source', `Upload ${view.toUpperCase()} View Photo`, [
      {
        text: '📷 Camera',
        onPress: async () => {
          const res = await cameraService.openCamera();
          if (res) validateAndSetPhoto(res, view);
        },
      },
      {
        text: '🖼️ Gallery',
        onPress: async () => {
          const res = await cameraService.openGallery();
          if (res) validateAndSetPhoto(res, view);
        },
      },
      { text: 'Cancel', style: 'cancel' },
    ]);
  };

  const validateAndSetPhoto = async (photo, view) => {
    if (view === 'front') {
      setFrontPhoto(photo);
      setValidatingFront(true);
    } else {
      setSidePhoto(photo);
      setValidatingSide(true);
    }

    try {
      const res = await uploadApi.uploadAndValidate(photo.uri, view);
      if (res.data?.person_count === 0) {
        Alert.alert('Warning', `No person detected in ${view} photo. Please select a clearer photo.`);
      }
    } catch (e) {
      console.log('Validation skipped:', e);
    } finally {
      if (view === 'front') setValidatingFront(false);
      else setValidatingSide(false);
    }
  };

  const handleProcess = async () => {
    if (!frontPhoto?.base64) {
      Alert.alert('Required', 'Please select a Front View photo');
      return;
    }
    if (!sidePhoto?.base64) {
      Alert.alert('Required', 'Please select a Side View photo');
      return;
    }
    if (!userHeight || isNaN(parseFloat(userHeight))) {
      Alert.alert('Required', 'Please enter a valid height in cm');
      return;
    }

    navigation.navigate('Processing', {
      frontB64: frontPhoto.base64,
      sideB64: sidePhoto.base64,
      heightCm: userHeight,
    });
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <Header title="Upload Photos" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.content}>
        <ErrorMessage message={error} />

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
          title={loading ? 'Processing...' : '⚡ Analyze & Calculate Measurements'}
          onPress={handleProcess}
          loading={loading}
          disabled={!frontPhoto || !sidePhoto}
          style={{ marginTop: 12 }}
        />
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 20, paddingBottom: 40 },
});

export default UploadScreen;
