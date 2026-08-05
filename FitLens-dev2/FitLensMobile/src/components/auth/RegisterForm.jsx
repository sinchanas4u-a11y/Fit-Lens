import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import Input from '../common/Input';
import Button from '../common/Button';
import ErrorMessage from '../common/ErrorMessage';

const RegisterForm = ({ onSubmit, loading, error }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});

  const handleSubmit = () => {
    const errs = {};
    if (!name) errs.name = 'Full name is required';
    if (!email) errs.email = 'Email address is required';
    if (!password) errs.password = 'Password is required';
    if (password && password.length < 8) errs.password = 'Min 8 characters';
    if (password !== confirmPassword) errs.confirmPassword = 'Passwords do not match';

    setFieldErrors(errs);
    if (Object.keys(errs).length === 0) {
      onSubmit(name.trim(), email.trim().toLowerCase(), password);
    }
  };

  return (
    <View style={styles.form}>
      <ErrorMessage message={error} />

      <Input
        label="Full Name"
        placeholder="John Doe"
        value={name}
        onChangeText={setName}
        error={fieldErrors.name}
        icon="👤"
      />

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

      <Input
        label="Confirm Password"
        placeholder="••••••••"
        value={confirmPassword}
        onChangeText={setConfirmPassword}
        secureTextEntry
        error={fieldErrors.confirmPassword}
        icon="🔒"
      />

      <Button
        title={loading ? 'Creating Account...' : 'Create Account'}
        onPress={handleSubmit}
        loading={loading}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  form: {},
});

export default RegisterForm;
