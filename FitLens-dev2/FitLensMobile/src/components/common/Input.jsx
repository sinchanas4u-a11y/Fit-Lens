import React, { useState } from 'react';
import { View, TextInput, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors } from '../../constants/colors';

const Input = ({
  label,
  placeholder,
  value,
  onChangeText,
  secureTextEntry,
  keyboardType = 'default',
  error,
  icon,
  style,
}) => {
  const [show, setShow] = useState(false);

  return (
    <View style={[styles.container, style]}>
      {label && <Text style={styles.label}>{label}</Text>}
      <View style={[styles.inputWrap, error && styles.inputError]}>
        {icon && <Text style={styles.icon}>{icon}</Text>}
        <TextInput
          style={styles.input}
          placeholder={placeholder}
          placeholderTextColor={Colors.textSecondary}
          value={value}
          onChangeText={onChangeText}
          secureTextEntry={secureTextEntry && !show}
          keyboardType={keyboardType}
          autoCapitalize="none"
        />
        {secureTextEntry && (
          <TouchableOpacity onPress={() => setShow(!show)} style={styles.eyeBtn}>
            <Text style={{ fontSize: 18 }}>{show ? '🙈' : '👁️'}</Text>
          </TouchableOpacity>
        )}
      </View>
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { marginBottom: 16 },
  label: {
    color: Colors.textSecondary,
    fontSize: 13,
    marginBottom: 8,
    fontWeight: '500',
  },
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.primary,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 10,
    paddingHorizontal: 16,
  },
  inputError: { borderColor: Colors.error },
  icon: { fontSize: 16, marginRight: 8 },
  input: {
    flex: 1,
    color: Colors.textPrimary,
    fontSize: 15,
    paddingVertical: 13,
  },
  eyeBtn: { padding: 4 },
  error: { color: Colors.error, fontSize: 12, marginTop: 4 },
});

export default Input;
