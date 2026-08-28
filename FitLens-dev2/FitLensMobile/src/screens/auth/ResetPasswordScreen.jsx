import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { authApi } from '../../api/authApi';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import Header from '../../components/common/Header';
import { Colors } from '../../constants/colors';

const ResetPasswordScreen = ({ route, navigation }) => {
  const routeToken = route?.params?.token || '';
  const [tokenInput, setTokenInput] = useState('');
  const token = routeToken || tokenInput.trim();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleReset = async () => {
    if (!newPassword || newPassword.length < 8) {
      Alert.alert('Error', 'Password must be at least 8 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      const res = await authApi.resetPassword(token, newPassword, confirmPassword);
      if (res.data.success) {
        Alert.alert('Success', 'Password reset successfully. Please log in.', [
          { text: 'OK', onPress: () => navigation.navigate('Login') },
        ]);
      }
    } catch (e) {
      Alert.alert('Reset Failed', e.response?.data?.error || 'Invalid or expired reset link');
    }
    setLoading(false);
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <Header title="Set New Password" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <Text style={styles.icon}>🔑</Text>
          <Text style={styles.title}>Create New Password</Text>
          <Text style={styles.subtitle}>Enter your new password below to reset your account credentials.</Text>

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
            title={loading ? 'Resetting Password...' : 'Reset Password'}
            onPress={handleReset}
            loading={loading}
          />
        </View>
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 24, justifyContent: 'center', flexGrow: 1 },
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
  },
  icon: { fontSize: 48, marginBottom: 12 },
  title: { color: Colors.textPrimary, fontSize: 20, fontWeight: '700', marginBottom: 8 },
  subtitle: { color: Colors.textSecondary, fontSize: 13, textAlign: 'center', marginBottom: 24 },
});

export default ResetPasswordScreen;
