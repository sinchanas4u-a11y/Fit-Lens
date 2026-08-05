import React from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { Colors } from '../../constants/colors';

const Loader = ({ message = 'Loading...' }) => (
  <View style={styles.container}>
    <ActivityIndicator size="large" color={Colors.accent} />
    {message ? <Text style={styles.text}>{message}</Text> : null}
  </View>
);

const styles = StyleSheet.create({
  container: {
    padding: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  text: {
    color: Colors.textSecondary,
    fontSize: 14,
    marginTop: 12,
    fontWeight: '500',
  },
});

export default Loader;
