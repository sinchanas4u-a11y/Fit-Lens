import React, { useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, StatusBar, Image } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { useAuthStore } from '../../store/authStore';
import { useMeasurementStore } from '../../store/measurementStore';
import { measurementApi } from '../../api/measurementApi';
import { Colors } from '../../constants/colors';

const brandLogo = require('../../assets/logo.png');

const HomeScreen = ({ navigation }) => {
  const { user } = useAuthStore();
  const { latestMeasurement, setLatest } = useMeasurementStore();

  useEffect(() => {
    fetchLatest();
  }, []);

  const fetchLatest = async () => {
    try {
      const res = await measurementApi.getLatest();
      if (res.data.latest) setLatest(res.data.latest);
    } catch {}
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <StatusBar barStyle="light-content" />
      <ScrollView contentContainerStyle={styles.content}>

        {/* Header */}
        <View style={styles.header}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Image source={brandLogo} style={{ width: 44, height: 44, marginRight: 12 }} resizeMode="contain" />
            <View>
              <Text style={styles.welcome}>Welcome back,</Text>
              <Text style={styles.name}>{user?.name || 'User'} 👋</Text>
            </View>
          </View>
          <TouchableOpacity onPress={() => navigation.navigate('Settings')}>
            <Text style={{ fontSize: 28 }}>⚙️</Text>
          </TouchableOpacity>
        </View>

        {/* Hero Card */}
        <View style={styles.heroCard}>
          <Text style={{ fontSize: 64 }}>🧍</Text>
          <Text style={styles.heroTitle}>Get Your Body Measurements</Text>
          <Text style={styles.heroSub}>
            Upload photos or use live camera for accurate AI measurements
          </Text>
        </View>

        {/* Previous scan banner */}
        {latestMeasurement && (
          <View style={styles.prevBanner}>
            <Text style={styles.prevTitle}>
              📊 Last Scan — {latestMeasurement.date}
            </Text>
            <Text style={styles.prevDetails}>
              Arm: {latestMeasurement.arm_length?.toFixed(1)}cm | Leg: {latestMeasurement.leg_length?.toFixed(1)}cm | Shoulder: {latestMeasurement.shoulder_width?.toFixed(1)}cm
            </Text>
            <View style={styles.prevButtons}>
              <TouchableOpacity
                style={styles.prevBtn}
                onPress={() => navigation.navigate('HistoryDetail', { measurement: latestMeasurement })}>
                <Text style={styles.prevBtnText}>View Details</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.prevBtn, styles.newBtn]}
                onPress={() => navigation.navigate('Guidelines')}>
                <Text style={[styles.prevBtnText, { color: Colors.accent }]}>New Scan</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Feature chips */}
        <View style={styles.chips}>
          {['🤖 YOLOv8', '🦴 MediaPipe', '🧊 3D Mesh', '📄 PDF Export'].map((chip) => (
            <View key={chip} style={styles.chip}>
              <Text style={styles.chipText}>{chip}</Text>
            </View>
          ))}
        </View>

        {/* Action Buttons */}
        <TouchableOpacity onPress={() => navigation.navigate('Guidelines')}>
          <LinearGradient
            colors={Colors.gradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.actionBtn}>
            <Text style={{ fontSize: 32 }}>📸</Text>
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={styles.actionTitle}>Upload Photos</Text>
              <Text style={styles.actionSub}>Front & side view</Text>
            </View>
            <Text style={{ color: '#fff', fontSize: 20 }}>›</Text>
          </LinearGradient>
        </TouchableOpacity>

        <TouchableOpacity
          style={{ marginTop: 12 }}
          onPress={() => navigation.navigate('Camera')}>
          <LinearGradient
            colors={['#7C3AED', '#0080FF']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.actionBtn}>
            <Text style={{ fontSize: 32 }}>🎥</Text>
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={styles.actionTitle}>Live Camera</Text>
              <Text style={styles.actionSub}>Real-time measurement</Text>
            </View>
            <Text style={{ color: '#fff', fontSize: 20 }}>›</Text>
          </LinearGradient>
        </TouchableOpacity>

      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 24, paddingTop: 48 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  welcome: { color: Colors.textSecondary, fontSize: 14 },
  name: { color: Colors.textPrimary, fontSize: 24, fontWeight: '700' },
  heroCard: {
    backgroundColor: Colors.cardBg,
    borderRadius: 20,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 20,
  },
  heroTitle: {
    color: Colors.textPrimary,
    fontSize: 20,
    fontWeight: '700',
    textAlign: 'center',
    marginTop: 12,
  },
  heroSub: { color: Colors.textSecondary, textAlign: 'center', marginTop: 8, fontSize: 13 },
  prevBanner: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.accent + '50',
    marginBottom: 20,
  },
  prevTitle: { color: Colors.accent, fontWeight: '700', marginBottom: 6 },
  prevDetails: { color: Colors.textSecondary, fontSize: 13, marginBottom: 12 },
  prevButtons: { flexDirection: 'row', gap: 8 },
  prevBtn: {
    flex: 1,
    padding: 8,
    borderRadius: 8,
    backgroundColor: Colors.secondary,
    alignItems: 'center',
  },
  newBtn: { borderWidth: 1, borderColor: Colors.accent, backgroundColor: 'transparent' },
  prevBtnText: { color: Colors.textSecondary, fontWeight: '600' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 24 },
  chip: {
    backgroundColor: Colors.cardBg,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chipText: { color: Colors.accent, fontSize: 12, fontWeight: '500' },
  actionBtn: { flexDirection: 'row', alignItems: 'center', padding: 20, borderRadius: 16 },
  actionTitle: { color: '#fff', fontSize: 18, fontWeight: '700' },
  actionSub: { color: 'rgba(255,255,255,0.8)', fontSize: 13 },
});

export default HomeScreen;
