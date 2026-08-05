import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/authApi';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import { Colors } from '../../constants/colors';

const LoginScreen = ({ navigation }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const { login } = useAuthStore();

  const validate = () => {
    const e = {};
    if (!email) e.email = 'Email is required';
    if (!password) e.password = 'Password is required';
    if (password && password.length < 8) e.password = 'Min 8 characters';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleLogin = async () => {
    if (!validate()) return;
    setLoading(true);
    try {
      const res = await authApi.login(email.trim().toLowerCase(), password);
      if (res.data.success) {
        await login(res.data.user, res.data.token);
      }
    } catch (err) {
      Alert.alert('Login Failed', err.response?.data?.error || 'Invalid email or password');
    }
    setLoading(false);
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.logo}>📏</Text>
        <Text style={styles.title}>FitLens AI</Text>
        <Text style={styles.subtitle}>AI-Powered Body Measurements</Text>

        <View style={styles.card}>
          <Text style={styles.heading}>Welcome Back</Text>

          <Input
            label="Email"
            placeholder="Enter your email"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            error={errors.email}
          />

          <Input
            label="Password"
            placeholder="Enter your password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            error={errors.password}
          />

          <TouchableOpacity
            onPress={() => navigation.navigate('ForgotPassword')}
            style={styles.forgot}>
            <Text style={styles.forgotText}>Forgot Password?</Text>
          </TouchableOpacity>

          <Button
            title={loading ? 'Logging in...' : 'Login'}
            onPress={handleLogin}
            loading={loading}
          />

          <TouchableOpacity
            onPress={() => navigation.navigate('Register')}
            style={styles.register}>
            <Text style={styles.registerText}>
              Don't have an account?{' '}
              <Text style={{ color: Colors.accent }}>Register</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  logo: { fontSize: 56, textAlign: 'center', marginBottom: 8 },
  title: { fontSize: 32, fontWeight: '800', color: Colors.accent, textAlign: 'center' },
  subtitle: { color: Colors.textSecondary, textAlign: 'center', marginBottom: 32, fontSize: 14 },
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  heading: { color: Colors.textPrimary, fontSize: 22, fontWeight: '700', marginBottom: 24, textAlign: 'center' },
  forgot: { alignSelf: 'flex-end', marginBottom: 16 },
  forgotText: { color: Colors.accent, fontSize: 13 },
  register: { marginTop: 16, alignItems: 'center' },
  registerText: { color: Colors.textSecondary, fontSize: 14 },
});

export default LoginScreen;
