import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import MeasurementBadge from './MeasurementBadge';
import { Colors } from '../../constants/colors';

const MeasurementTable = ({ measurements }) => {
  if (!measurements || Object.keys(measurements).length === 0) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyText}>No measurement data available</Text>
      </View>
    );
  }

  const renderRow = (key, value) => {
    const name = key.replace(/_/g, ' ').toUpperCase();
    let cm = '--';
    let source = 'Unknown';

    if (typeof value === 'object' && value !== null) {
      cm = value.value_cm !== undefined ? value.value_cm.toFixed(1) : '--';
      source = value.source || 'Unknown';
    } else if (typeof value === 'number') {
      cm = value.toFixed(1);
    }

    return (
      <View key={key} style={styles.row}>
        <Text style={styles.name}>{name}</Text>
        <Text style={styles.val}>{cm} cm</Text>
        <MeasurementBadge source={source} />
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {Object.entries(measurements).map(([k, v]) => renderRow(k, v))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {},
  empty: { padding: 16, alignItems: 'center' },
  emptyText: { color: Colors.textSecondary, fontSize: 13 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  name: { flex: 1, color: Colors.textSecondary, fontSize: 13 },
  val: { color: Colors.accent, fontWeight: '700', fontSize: 15, marginRight: 8 },
});

export default MeasurementTable;
