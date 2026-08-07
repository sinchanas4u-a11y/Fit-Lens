import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert, Image } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { authApi } from '../../api/authApi';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import { Colors } from '../../constants/colors';

const brandLogo = require('../../assets/logo.png');

const RegisterScreen = ({ navigation }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const e = {};
    if (!name) e.name = 'Name is required';
    if (!email) e.email = 'Email is required';
    if (!password) e.password = 'Password is required';
    if (password && password.length < 8) e.password = 'Min 8 characters';
    if (password !== confirmPassword) e.confirmPassword = 'Passwords do not match';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleRegister = async () => {
    if (!validate()) return;
    setLoading(true);
    try {
      const res = await authApi.register(name.trim(), email.trim().toLowerCase(), password);
      if (res.data.success) {
        Alert.alert('Success', 'Account created successfully! Please login.', [
          { text: 'OK', onPress: () => navigation.navigate('Login') },
        ]);
      }
    } catch (err) {
      Alert.alert('Registration Failed', err.response?.data?.error || 'Could not register account');
    }
    setLoading(false);
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Image source={brandLogo} style={styles.logoHeader} resizeMode="contain" />

        <View style={styles.card}>
          <Text style={styles.heading}>Create Account</Text>

          <Input
            label="Full Name"
            placeholder="Enter your name"
            value={name}
            onChangeText={setName}
            error={errors.name}
          />

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
            placeholder="Min 8 characters"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            error={errors.password}
          />

          <Input
            label="Confirm Password"
            placeholder="Re-enter password"
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            secureTextEntry
            error={errors.confirmPassword}
          />

          <Button
            title={loading ? 'Registering...' : 'Register'}
            onPress={handleRegister}
            loading={loading}
          />

          <TouchableOpacity
            onPress={() => navigation.navigate('Login')}
            style={styles.loginLink}>
            <Text style={styles.loginText}>
              Already have an account?{' '}
              <Text style={{ color: Colors.accent }}>Login</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { flexGrow: 1, justifyContent: 'center', padding: 24, paddingVertical: 40 },
  logoHeader: { width: 200, height: 160, alignSelf: 'center', marginBottom: 16 },
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  heading: { color: Colors.textPrimary, fontSize: 20, fontWeight: '700', marginBottom: 20, textAlign: 'center' },
  loginLink: { marginTop: 16, alignItems: 'center' },
  loginText: { color: Colors.textSecondary, fontSize: 14 },
});

export default RegisterScreen;
