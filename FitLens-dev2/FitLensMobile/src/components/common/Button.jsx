import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { Colors } from '../../constants/colors';

const Button = ({ title, onPress, loading, variant = 'primary', style, textStyle, disabled }) => {
  if (variant === 'primary') {
    return (
      <TouchableOpacity onPress={onPress} disabled={loading || disabled} style={[styles.touch, style]}>
        <LinearGradient
          colors={Colors.gradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={[styles.gradient, disabled && styles.disabled]}>
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={[styles.primaryText, textStyle]}>{title}</Text>
          )}
        </LinearGradient>
      </TouchableOpacity>
    );
  }

  if (variant === 'danger') {
    return (
      <TouchableOpacity
        onPress={onPress}
        disabled={loading || disabled}
        style={[styles.dangerBtn, disabled && styles.disabled, style]}>
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={[styles.dangerText, textStyle]}>{title}</Text>
        )}
      </TouchableOpacity>
    );
  }

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={loading || disabled}
      style={[styles.secondary, disabled && styles.disabled, style]}>
      {loading ? (
        <ActivityIndicator color={Colors.accent} />
      ) : (
        <Text style={[styles.secondaryText, textStyle]}>{title}</Text>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  touch: { borderRadius: 12, overflow: 'hidden' },
  gradient: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  secondary: {
    paddingVertical: 13,
    paddingHorizontal: 24,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    backgroundColor: Colors.secondary,
  },
  secondaryText: { color: Colors.textSecondary, fontSize: 15, fontWeight: '600' },
  dangerBtn: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    backgroundColor: '#E53E3E',
    alignItems: 'center',
  },
  dangerText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  disabled: { opacity: 0.5 },
});

export default Button;
