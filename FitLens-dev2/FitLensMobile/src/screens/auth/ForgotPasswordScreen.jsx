import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert, TouchableOpacity } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { authApi } from '../../api/authApi';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import Header from '../../components/common/Header';
import { Colors } from '../../constants/colors';

const ForgotPasswordScreen = ({ navigation }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSend = async () => {
    if (!email) {
      Alert.alert('Error', 'Please enter your registered email address');
      return;
    }
    setLoading(true);
    try {
      await authApi.forgotPassword(email.trim().toLowerCase());
      setSent(true);
    } catch (e) {
      Alert.alert('Notice', "If an account exists for this email address, we've sent a password reset link. Please check your inbox.");
    }
    setLoading(false);
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <Header title="Forgot Password" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <Text style={styles.icon}>✉️</Text>
          <Text style={styles.title}>Reset Your Password</Text>
          <Text style={styles.subtitle}>
            Enter your account email address. We will send a secure password reset link to your inbox.
          </Text>

          {sent ? (
            <View style={styles.sentBox}>
              <Text style={styles.sentText}>
                If an account exists for this email address, we've sent a password reset link. Please check your inbox.
              </Text>
              <Button
                title="Back to Login"
                onPress={() => navigation.navigate('Login')}
                style={{ marginTop: 20 }}
              />
            </View>
          ) : (
            <>
              <Input
                label="Registered Email"
                placeholder="name@example.com"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
              />

              <Button
                title={loading ? 'Sending Request...' : 'Send Reset Link'}
                onPress={handleSend}
                loading={loading}
              />
            </>
          )}
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
  subtitle: { color: Colors.textSecondary, fontSize: 13, textAlign: 'center', marginBottom: 24, lineHeight: 18 },
  sentBox: { width: '100%', alignItems: 'center' },
  sentText: { color: Colors.accent, fontSize: 14, textAlign: 'center', lineHeight: 20 },
});

export default ForgotPasswordScreen;
