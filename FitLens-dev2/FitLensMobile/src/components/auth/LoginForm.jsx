import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Text } from 'react-native';
import Input from '../common/Input';
import Button from '../common/Button';
import ErrorMessage from '../common/ErrorMessage';
import { Colors } from '../../constants/colors';

const LoginForm = ({ onSubmit, onForgotPassword, loading, error }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});

  const handleSubmit = () => {
    const errs = {};
    if (!email) errs.email = 'Email is required';
    if (!password) errs.password = 'Password is required';
    if (password && password.length < 8) errs.password = 'Min 8 characters';
    
    setFieldErrors(errs);
    if (Object.keys(errs).length === 0) {
      onSubmit(email.trim().toLowerCase(), password);
    }
  };

  return (
    <View style={styles.form}>
      <ErrorMessage message={error} />

      <Input
        label="Email Address"
        placeholder="name@example.com"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        error={fieldErrors.email}
        icon="✉️"
      />

      <Input
        label="Password"
        placeholder="••••••••"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        error={fieldErrors.password}
        icon="🔒"
      />

      {onForgotPassword && (
        <TouchableOpacity onPress={onForgotPassword} style={styles.forgotBtn}>
          <Text style={styles.forgotText}>Forgot Password?</Text>
        </TouchableOpacity>
      )}

      <Button
        title={loading ? 'Logging in...' : 'Sign In'}
        onPress={handleSubmit}
        loading={loading}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  form: {},
  forgotBtn: { alignSelf: 'flex-end', marginBottom: 20 },
  forgotText: { color: Colors.accent, fontSize: 13, fontWeight: '600' },
});

export default LoginForm;
