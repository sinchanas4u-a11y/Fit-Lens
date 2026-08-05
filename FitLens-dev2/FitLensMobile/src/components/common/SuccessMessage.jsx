import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../../constants/colors';

const SuccessMessage = ({ message, style }) => {
  if (!message) return null;
  return (
    <View style={[styles.container, style]}>
      <Text style={styles.icon}>✅</Text>
      <Text style={styles.text}>{message}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#48BB7820',
    borderWidth: 1,
    borderColor: Colors.success,
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  icon: { fontSize: 16, marginRight: 8 },
  text: { color: Colors.success, fontSize: 13, flex: 1, fontWeight: '500' },
});

export default SuccessMessage;
