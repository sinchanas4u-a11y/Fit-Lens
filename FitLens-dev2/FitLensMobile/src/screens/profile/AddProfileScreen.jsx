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
import { useProfileStore } from '../../store/profileStore';
import { Colors } from '../../constants/colors';

const RELATIONSHIPS = [
  'Self',
  'Spouse',
  'Child',
  'Parent',
  'Sibling',
  'Friend',
  'Other',
];

const AddProfileScreen = ({ navigation }) => {
  const [name, setName] = useState('');
  const [relationship, setRelationship] = useState('Friend');
  const [profileType, setProfileType] = useState('adult'); // 'adult' | 'child'
  const [heightCm, setHeightCm] = useState('170');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { createProfile, setActiveProfile, activeProfile } = useProfileStore();

  const isCallerOwner = !activeProfile || Boolean(activeProfile?.is_owner || activeProfile?.profile_type === 'owner');

  const handleRelationshipSelect = (rel) => {
    setRelationship(rel);
    if (rel === 'Child') {
      setProfileType('child');
    }
  };

  const handleProfileTypeSelect = (type) => {
    setProfileType(type);
    if (type === 'child' && relationship !== 'Child') {
      setRelationship('Child');
    }
  };

  const handleSubmit = async () => {
    if (!isCallerOwner) {
      Alert.alert('Permission Denied', 'Only the primary account owner has permission to create new profiles.');
      return;
    }

    const trimmedName = name.trim();
    if (!trimmedName || trimmedName.length < 1 || trimmedName.length > 50) {
      Alert.alert('Invalid Name', 'Profile name must be between 1 and 50 characters.');
      return;
    }

    const parsedHeight = parseFloat(heightCm);
    if (isNaN(parsedHeight) || parsedHeight < 100 || parsedHeight > 250) {
      Alert.alert('Invalid Height', 'Default height must be between 100 cm and 250 cm.');
      return;
    }

    setIsSubmitting(true);
    const result = await createProfile({
      name: trimmedName,
      relationship,
      profile_type: profileType,
      default_height_cm: parsedHeight,
    });
    setIsSubmitting(false);

    if (result.success) {
      Alert.alert(
        'Profile Created',
        `Profile for "${trimmedName}" has been added to your FitLens account.`,
        [
          {
            text: 'Use Profile Now',
            onPress: async () => {
              if (result.profile) {
                await setActiveProfile(result.profile);
              }
              navigation.navigate('Tabs');
            },
          },
          {
            text: 'Done',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } else {
      Alert.alert('Could Not Create Profile', result.error || 'Failed to create profile.');
    }
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <StatusBar barStyle="light-content" />
      <Header title="Add New Profile" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Name input */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>Profile Name *</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., Sarah, Alex, Mom"
            placeholderTextColor={Colors.textSecondary}
            value={name}
            onChangeText={setName}
            maxLength={50}
          />
        </View>

        {/* Profile Type Toggle */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>Profile Type</Text>
          <View style={styles.toggleRow}>
            <TouchableOpacity
              style={[styles.toggleBtn, profileType === 'adult' && styles.toggleBtnActive]}
              onPress={() => handleProfileTypeSelect('adult')}>
              <Text style={[styles.toggleText, profileType === 'adult' && styles.toggleTextActive]}>
                Adult Member
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.toggleBtn, profileType === 'child' && styles.toggleBtnActive]}
              onPress={() => handleProfileTypeSelect('child')}>
              <Text style={[styles.toggleText, profileType === 'child' && styles.toggleTextActive]}>
                Child / Minor
              </Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.helperText}>
            {profileType === 'child'
              ? 'Child profiles are managed directly by the account owner without separate device invites.'
              : 'Adult profiles can be managed directly or invited to scan independently.'}
          </Text>
        </View>

        {/* Relationship Picker */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>Relationship to Account Owner</Text>
          <View style={styles.pillsRow}>
            {RELATIONSHIPS.map((rel) => {
              const isSelected = relationship === rel;
              return (
                <TouchableOpacity
                  key={rel}
                  style={[styles.pill, isSelected && styles.pillActive]}
                  onPress={() => handleRelationshipSelect(rel)}>
                  <Text style={[styles.pillText, isSelected && styles.pillTextActive]}>
                    {rel}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* Default Height Input */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>Default Height (cm) *</Text>
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
            FitLens uses height for optical calibration to calculate centimeter-accurate body circumferences.
          </Text>
        </View>

        {/* Submit Button */}
        <TouchableOpacity
          style={styles.submitBtn}
          onPress={handleSubmit}
          disabled={isSubmitting}>
          <LinearGradient
            colors={Colors.gradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.gradientBtn}>
            {isSubmitting ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.submitText}>Save Profile</Text>
            )}
          </LinearGradient>
        </TouchableOpacity>
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { padding: 20, paddingBottom: 40 },
  formGroup: { marginBottom: 24 },
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
  toggleRow: {
    flexDirection: 'row',
    gap: 12,
  },
  toggleBtn: {
    flex: 1,
    backgroundColor: Colors.cardBg,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  toggleBtnActive: {
    borderColor: Colors.accent,
    backgroundColor: 'rgba(0, 212, 170, 0.15)',
  },
  toggleText: {
    color: Colors.textSecondary,
    fontSize: 13,
    fontWeight: '600',
  },
  toggleTextActive: {
    color: Colors.accent,
    fontWeight: '700',
  },
  pillsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  pill: {
    backgroundColor: Colors.cardBg,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  pillActive: {
    backgroundColor: Colors.accent,
    borderColor: Colors.accent,
  },
  pillText: {
    color: Colors.textSecondary,
    fontSize: 13,
    fontWeight: '600',
  },
  pillTextActive: {
    color: Colors.primary,
    fontWeight: '700',
  },
  heightRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  heightInput: {
    flex: 1,
  },
  unitText: {
    color: Colors.textSecondary,
    fontSize: 16,
    fontWeight: '700',
    marginLeft: 12,
  },
  helperText: {
    color: Colors.textSecondary,
    fontSize: 12,
    marginTop: 6,
    lineHeight: 16,
  },
  submitBtn: {
    marginTop: 12,
  },
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
});

export default AddProfileScreen;
