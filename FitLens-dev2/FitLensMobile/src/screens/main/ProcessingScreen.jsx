import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import * as Progress from 'react-native-progress';
import { uploadApi } from '../../api/uploadApi';
import { useMeasurementStore } from '../../store/measurementStore';
import { Colors } from '../../constants/colors';

const ProcessingScreen = ({ route, navigation }) => {
  const { frontB64, sideB64, heightCm } = route.params;
  const [progress, setProgress] = useState(0.1);
  const [stepText, setStepText] = useState('Initializing AI Pipeline...');
  const { setCurrentResults } = useMeasurementStore();

  const steps = [
    { target: 0.25, text: '🔍 Detecting Pose Keypoints (MediaPipe)' },
    { target: 0.50, text: '🤖 Generating YOLOv8 Body Segmentations' },
    { target: 0.75, text: '📏 Calibrating Pixel-to-Scale Ratios' },
    { target: 0.90, text: '🧊 Reconstructing 3D Mesh Model (SMPL)' },
    { target: 1.00, text: '✨ Finalizing Measurement Report...' },
  ];

  useEffect(() => {
    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep < steps.length) {
        setProgress(steps[currentStep].target);
        setStepText(steps[currentStep].text);
        currentStep += 1;
      } else {
        clearInterval(interval);
      }
    }, 1500);

    runAnalysis();

    return () => clearInterval(interval);
  }, []);

  const runAnalysis = async () => {
    try {
      const res = await uploadApi.processUpload(frontB64, sideB64, parseFloat(heightCm));
      if (res.success || res.results) {
        setCurrentResults(res);
        navigation.replace('Results', { data: res });
      } else {
        throw new Error(res.error || 'Failed to generate measurements');
      }
    } catch (e) {
      Alert.alert(
        'Processing Error',
        e.response?.data?.error || e.message || 'AI processing encountered an error',
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
