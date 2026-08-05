import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors } from '../../constants/colors';

const Header = ({ title, onBack, rightElement }) => (
  <View style={styles.header}>
    {onBack ? (
      <TouchableOpacity onPress={onBack} style={styles.backBtn}>
        <Text style={styles.backText}>←</Text>
      </TouchableOpacity>
    ) : (
      <View style={styles.placeholder} />
    )}
    <Text style={styles.title} numberOfLines={1}>{title}</Text>
    {rightElement ? (
      <View style={styles.right}>{rightElement}</View>
    ) : (
      <View style={styles.placeholder} />
    )}
  </View>
);

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: Colors.secondary,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backBtn: { padding: 4 },
  backText: { color: Colors.textPrimary, fontSize: 24 },
  title: { color: Colors.textPrimary, fontSize: 18, fontWeight: '700', textAlign: 'center', flex: 1 },
  placeholder: { width: 32 },
  right: { alignItems: 'flex-end' },
});

export default Header;
