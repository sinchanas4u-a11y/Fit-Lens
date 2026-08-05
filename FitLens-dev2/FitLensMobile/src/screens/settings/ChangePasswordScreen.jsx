import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Header from '../../components/common/Header';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import { authApi } from '../../api/authApi';
import { Colors } from '../../constants/colors';

const ChangePasswordScreen = ({ navigation }) => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChangePassword = async () => {
    if (!currentPassword) {
      Alert.alert('Error', 'Please enter your current password');
      return;
    }
    if (!newPassword || newPassword.length < 8) {
      Alert.alert('Error', 'New password must be at least 8 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      Alert.alert('Error', 'New passwords do not match');
      return;
    }

    setLoading(true);
    try {
      const res = await authApi.changePassword(currentPassword, newPassword, confirmPassword);
      if (res.data.success) {
        Alert.alert('Success', 'Password changed successfully.', [
          { text: 'OK', onPress: () => navigation.goBack() },
        ]);
      }
    } catch (e) {
      Alert.alert('Change Failed', e.response?.data?.error || 'Could not change password');
    }
    setLoading(false);
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <Header title="Change Password" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>🔒 Change Security Password</Text>

          <Input
            label="Current Password"
            placeholder="Enter current password"
            value={currentPassword}
            onChangeText={setCurrentPassword}
            secureTextEntry
          />

          <Input
            label="New Password"
            placeholder="Min 8 characters"
            value={newPassword}
            onChangeText={setNewPassword}
            secureTextEntry
          />

          <Input
            label="Confirm New Password"
            placeholder="Re-enter new password"
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            secureTextEntry
          />

          <Button
            title={loading ? 'Updating Password...' : 'Update Password'}
            onPress={handleChangePassword}
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

export default ChangePasswordScreen;
