import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Header from '../../components/common/Header';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/authApi';
import { Colors } from '../../constants/colors';

const ProfileSettings = ({ navigation }) => {
  const { user, setUser } = useAuthStore();
  const [name, setName] = useState(user?.name || '');
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Name cannot be empty');
      return;
    }

    setLoading(true);
    try {
      const res = await authApi.updateProfile(name.trim());
      if (res.data.success) {
        setUser({ ...user, name: name.trim() });
        Alert.alert('Success', 'Profile updated successfully!');
      }
    } catch (e) {
      Alert.alert('Error', e.response?.data?.error || 'Could not update profile');
    }
    setLoading(false);
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <Header title="Profile Settings" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>👤 Personal Information</Text>

          <Input label="Full Name" value={name} onChangeText={setName} />

          <Input
            label="Email Address (Read Only)"
            value={user?.email || ''}
            onChangeText={() => {}}
            style={{ opacity: 0.7 }}
          />

          <Button
            title={loading ? 'Saving...' : 'Save Profile Changes'}
            onPress={handleSave}
            loading={loading}
            style={{ marginTop: 12 }}
          />
        </View>
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16 },
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sectionTitle: { color: Colors.textPrimary, fontSize: 18, fontWeight: '700', marginBottom: 20 },
});

export default ProfileSettings;
