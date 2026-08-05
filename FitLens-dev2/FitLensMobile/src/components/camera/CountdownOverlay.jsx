import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../../constants/colors';

const CountdownOverlay = ({ seconds }) => {
  if (!seconds || seconds <= 0) return null;

  return (
    <View style={styles.overlay} pointerEvents="none">
      <View style={styles.circle}>
        <Text style={styles.number}>{seconds}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(10, 14, 39, 0.4)',
  },
  circle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: Colors.accent + 'DD',
    justifyContent: 'center',
    alignItems: 'center',
  },
  number: {
    fontSize: 64,
    fontWeight: '900',
    color: Colors.primary,
  },
});

export default CountdownOverlay;
