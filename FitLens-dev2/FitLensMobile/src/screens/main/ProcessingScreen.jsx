import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import * as Progress from 'react-native-progress';
import RNFS from 'react-native-fs';
import axiosInstance from '../../api/axiosInstance';
import { useMeasurementStore } from '../../store/measurementStore';
import useAuthStore from '../../store/authStore';
import { Colors } from '../../constants/colors';

const ProcessingScreen = ({ route, navigation }) => {
  const { frontImageUri, sideImageUri, userHeightCm, frontB64, sideB64, heightCm } = route.params;
  const targetHeight = userHeightCm || parseFloat(heightCm) || 165;
  const [progress, setProgress] = useState(0.1);
  const [stepText, setStepText] = useState('Converting images...');
  const { setCurrentResults } = useMeasurementStore();
  const logout = useAuthStore((state) => state.logout);

  useEffect(() => {
    processImages();
  }, []);

  const verifyFaceMatch = async (frontBase64) => {
    try {
      const res = await axiosInstance.post('/api/auth/verify-face', {
        front_image: frontBase64,
      });
      if (res.data && !res.data.verified) {
        Alert.alert(
          '⚠️ Identity Mismatch',
          'The scanned person does not match the account owner. Measurements will not be saved.',
          [
            { text: '🔄 Scan Again', onPress: () => navigation.goBack() },
            { text: '📊 Continue Without Saving', onPress: () => processWithoutSaving(frontBase64) },
            { text: '🚪 Switch Account', onPress: () => logout() },
          ]
        );
        return false;
      }
      return true;
    } catch (e) {
      console.log('Face verify skipped or unavailable:', e);
      return true; // If verification unavailable, proceed
    }
  };

  const processWithoutSaving = async (frontBase64) => {
    try {
      let sideBase64 = sideB64;
      if (!sideBase64 && sideImageUri) {
        const sideRaw = await RNFS.readFile(sideImageUri.replace('file://', ''), 'base64');
        sideBase64 = `data:image/jpeg;base64,${sideRaw}`;
      }

      setStepText('Analyzing measurements...');
      setProgress(0.6);

      const res = await axiosInstance.post('/api/process', {
        front_image: frontBase64,
        side_image: sideBase64,
        user_height: targetHeight,
      }, { timeout: 300000 });

      if (res.data?.success) {
        setCurrentResults(res.data);
        navigation.replace('Results', { data: res.data });
      } else {
        throw new Error(res.data?.error || 'Processing failed');
      }
    } catch (err) {
      Alert.alert(
        'Processing Error',
        err.response?.data?.error || err.message || 'Failed to generate measurements',
        [{ text: 'Go Back', onPress: () => navigation.goBack() }]
      );
    }
  };

  const processImages = async () => {
    try {
      setStepText('Converting images...');
      setProgress(0.2);

      let frontBase64 = frontB64;
      let sideBase64 = sideB64;

      if (!frontBase64 && frontImageUri) {
        const frontRaw = await RNFS.readFile(frontImageUri.replace('file://', ''), 'base64');
        frontBase64 = `data:image/jpeg;base64,${frontRaw}`;
      } else if (frontBase64 && !frontBase64.startsWith('data:')) {
        frontBase64 = `data:image/jpeg;base64,${frontBase64}`;
      }

      if (!sideBase64 && sideImageUri) {
        const sideRaw = await RNFS.readFile(sideImageUri.replace('file://', ''), 'base64');
        sideBase64 = `data:image/jpeg;base64,${sideRaw}`;
      } else if (sideBase64 && !sideBase64.startsWith('data:')) {
        sideBase64 = `data:image/jpeg;base64,${sideBase64}`;
      }

      setStepText('Verifying identity...');
      setProgress(0.4);
      const faceVerified = await verifyFaceMatch(frontBase64);
      if (!faceVerified) return;

      setStepText('Analyzing measurements...');
      setProgress(0.7);

      const res = await axiosInstance.post('/api/process', {
        front_image: frontBase64,
        side_image: sideBase64,
        user_height: targetHeight,
      }, {
        timeout: 300000, // 5 minutes for processing
      });

      if (res.data?.success) {
        setStepText('Finalizing results...');
        setProgress(0.95);

        // Save measurements to MongoDB:
        try {
          const measurements = res.data.results?.merged?.measurements ||
            res.data.results?.front?.measurements || {};
          await axiosInstance.post('/api/measurements/save', {
            measurements,
            user_height: targetHeight,
            source: 'upload',
          });
        } catch (saveErr) {
          console.log('Save error (non-critical):', saveErr);
        }

        setProgress(1.0);
        setCurrentResults(res.data);
        navigation.replace('Results', { data: res.data });
      } else {
        throw new Error(res.data?.error || 'Processing failed');
      }
    } catch (err) {
      console.log('Processing error:', err.response?.data || err.message);
      Alert.alert(
        'Processing Error',
        err.response?.data?.error || err.message || 'Failed to generate measurements',
        [{ text: 'Go Back', onPress: () => navigation.goBack() }]
      );
    }
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <View style={styles.content}>
        <ActivityIndicator size="large" color={Colors.accent} style={styles.spinner} />
        
        <Text style={styles.title}>Processing AI Analysis</Text>
        <Text style={styles.sub}>Please wait while our multi-stage AI models calculate your exact dimensions.</Text>

        <View style={styles.progressWrap}>
          <Progress.Bar
            progress={progress}
            width={280}
            height={10}
            color={Colors.accent}
            unfilledColor={Colors.secondary}
            borderColor={Colors.border}
            borderRadius={5}
          />
          <Text style={styles.stepText}>{stepText}</Text>
        </View>
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  content: { padding: 32, alignItems: 'center', width: '100%' },
  spinner: { transform: [{ scale: 1.4 }], marginBottom: 24 },
  title: { color: Colors.textPrimary, fontSize: 22, fontWeight: '800', textAlign: 'center', marginBottom: 8 },
  sub: { color: Colors.textSecondary, fontSize: 13, textAlign: 'center', marginBottom: 32, lineHeight: 18 },
  progressWrap: { alignItems: 'center' },
  stepText: { color: Colors.accent, fontSize: 13, fontWeight: '600', marginTop: 16, textAlign: 'center' },
});

export default ProcessingScreen;
