import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Colors } from '../../constants/colors';

const Card = ({ children, style }) => (
  <View style={[styles.card, style]}>{children}</View>
);

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
});

export default Card;
