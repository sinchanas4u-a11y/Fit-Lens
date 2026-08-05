import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../../constants/colors';

const MeasurementBadge = ({ source }) => {
  const src = source || 'Unknown';
  let badgeColor = Colors.warning;
  if (src.includes('SMPL')) badgeColor = '#7C3AED';
  else if (src.includes('MediaPipe')) badgeColor = Colors.accent;

  return (
    <View style={[styles.badge, { backgroundColor: badgeColor + '30', borderColor: badgeColor }]}>
      <Text style={[styles.badgeText, { color: badgeColor }]}>
        {src.split(' ')[0]}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    borderWidth: 1,
  },
  badgeText: { fontSize: 10, fontWeight: '600' },
});

export default MeasurementBadge;
