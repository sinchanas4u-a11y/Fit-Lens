import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  StatusBar,
  Alert,
  ActivityIndicator,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Header from '../../components/common/Header';
import { profileApi } from '../../api/profileApi';
import { Colors } from '../../constants/colors';

const JoinAccountScreen = ({ navigation, route }) => {
  const initialCode = route?.params?.code || '';
  const [inviteCode, setInviteCode] = useState(initialCode);
  const [name, setName] = useState('');
  const [heightCm, setHeightCm] = useState('170');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleClaim = async () => {
    const trimmedCode = inviteCode.trim().toUpperCase();
    if (!trimmedCode) {
      Alert.alert('Required', 'Please enter your FitLens invitation code.');
      return;
    }

    const trimmedName = name.trim();
    if (!trimmedName || trimmedName.length < 1 || trimmedName.length > 50) {
      Alert.alert('Required', 'Please enter your name (1 to 50 characters).');
      return;
    }

    const parsedHeight = parseFloat(heightCm);
    if (isNaN(parsedHeight) || parsedHeight < 100 || parsedHeight > 250) {
      Alert.alert('Invalid Height', 'Please enter a valid height between 100 cm and 250 cm.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await profileApi.claimInvite({
        invite_code: trimmedCode,
        name: trimmedName,
        default_height_cm: parsedHeight,
      });

      if (res.data?.success) {
        Alert.alert(
          'Profile Created',
          "Your FitLens profile has been created successfully.\n\nIn the current version, ask the account owner to select your profile when using the shared FitLens account.\n\nPrivate profile unlock with your own PIN will be available in a future update.",
          [
            {
              text: 'OK',
              onPress: () => navigation.navigate('Login'),
            },
          ]
        );
      } else {
        Alert.alert('Claim Failed', res.data?.error || 'Invalid or expired invite.');
      }
    } catch (err) {
      const msg = err.response?.data?.error || err.message || 'Could not claim invitation code.';
      Alert.alert('Claim Failed', msg);
    }
    setIsSubmitting(false);
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <StatusBar barStyle="light-content" />
      <Header title="Join FitLens Account" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.introCard}>
          <Text style={styles.introEmoji}>🤝</Text>
          <Text style={styles.introTitle}>Accept Profile Invitation</Text>
          <Text style={styles.introSub}>
            Enter the 15-minute invite code provided by the account owner to create your personal measurement profile.
          </Text>
        </View>

        {/* Phase 1 Shared Privacy Notice */}
        <View style={styles.privacyCard}>
          <View style={styles.privacyHeader}>
            <Text style={styles.privacyIcon}>ℹ️</Text>
            <Text style={styles.privacyTitle}>Phase 1 Privacy Disclosure</Text>
          </View>
          <Text style={styles.privacyText}>
            Notice: In Phase 1, profiles within this account share access. Any member logged into this account can view body measurements across all profiles. Private profile locking with PINs will be available in an upcoming update.
          </Text>
        </View>

        {/* Invite Code Input */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>Invitation Code *</Text>
          <TextInput
            style={[styles.input, styles.codeInput]}
            placeholder="e.g. FL-A8K2-9D31"
            placeholderTextColor={Colors.textSecondary}
            value={inviteCode}
            onChangeText={(txt) => setInviteCode(txt.toUpperCase())}
            autoCapitalize="characters"
            maxLength={20}
          />
          <Text style={styles.helperText}>
            Enter the 8-character code or deep-link token received from the account owner.
          </Text>
        </View>

        {/* Name Input */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>Your Name *</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. Sarah Connor"
            placeholderTextColor={Colors.textSecondary}
            value={name}
            onChangeText={setName}
            maxLength={50}
          />
        </View>

        {/* Default Height Input */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>Your Height (cm) *</Text>
          <View style={styles.heightRow}>
            <TextInput
              style={[styles.input, styles.heightInput]}
              placeholder="170"
              placeholderTextColor={Colors.textSecondary}
              value={heightCm}
              onChangeText={setHeightCm}
              keyboardType="numeric"
              maxLength={5}
            />
            <Text style={styles.unitText}>cm</Text>
          </View>
          <Text style={styles.helperText}>
            Required for optical scale calibration and accurate AI circumference measurement.
          </Text>
        </View>

        {/* Submit Claim Button */}
        <TouchableOpacity
          style={styles.submitBtn}
          onPress={handleClaim}
          disabled={isSubmitting}>
          <LinearGradient
            colors={Colors.gradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.gradientBtn}>
            {isSubmitting ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.submitText}>Claim Invitation & Join</Text>
            )}
          </LinearGradient>
        </TouchableOpacity>

        {/* Back to Login link */}
        <TouchableOpacity
          style={styles.loginLink}
          onPress={() => navigation.navigate('Login')}>
          <Text style={styles.loginLinkText}>
            Already have an account? <Text style={{ color: Colors.accent }}>Log In</Text>
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { padding: 20, paddingBottom: 40 },
  introCard: {
    alignItems: 'center',
    marginBottom: 20,
  },
  introEmoji: { fontSize: 48, marginBottom: 8 },
  introTitle: {
    color: Colors.textPrimary,
    fontSize: 22,
    fontWeight: '800',
    textAlign: 'center',
  },
  introSub: {
    color: Colors.textSecondary,
    fontSize: 13,
    textAlign: 'center',
    marginTop: 6,
    lineHeight: 18,
  },
  privacyCard: {
    backgroundColor: 'rgba(0, 128, 255, 0.1)',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 128, 255, 0.3)',
    marginBottom: 24,
  },
  privacyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  privacyIcon: { fontSize: 16, marginRight: 8 },
  privacyTitle: {
    color: Colors.accentBlue,
    fontSize: 13,
    fontWeight: '700',
  },
  privacyText: {
    color: Colors.textSecondary,
    fontSize: 12,
    lineHeight: 18,
  },
  formGroup: { marginBottom: 20 },
  label: {
    color: Colors.textPrimary,
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 8,
  },
  input: {
    backgroundColor: Colors.cardBg,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: Colors.textPrimary,
    fontSize: 15,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  codeInput: {
    letterSpacing: 2,
    fontWeight: '700',
    color: Colors.accent,
  },
  heightRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  heightInput: { flex: 1 },
  unitText: {
    color: Colors.textSecondary,
    fontSize: 16,
    fontWeight: '700',
    marginLeft: 12,
  },
  helperText: {
    color: Colors.textSecondary,
    fontSize: 11,
    marginTop: 6,
    lineHeight: 15,
  },
  submitBtn: { marginTop: 12 },
  gradientBtn: {
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
  },
  submitText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
  loginLink: {
    marginTop: 20,
    alignItems: 'center',
  },
  loginLinkText: {
    color: Colors.textSecondary,
    fontSize: 14,
  },
});

export default JoinAccountScreen;
