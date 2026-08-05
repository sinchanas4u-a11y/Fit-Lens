import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors } from '../../constants/colors';

const MeasurementCard = ({ item, onPress, onDelete }) => {
  const date = item.date || item.created_at || 'Unknown Date';
  const arm = item.arm_length ? `${item.arm_length.toFixed(1)} cm` : '--';
  const leg = item.leg_length ? `${item.leg_length.toFixed(1)} cm` : '--';
  const shoulder = item.shoulder_width ? `${item.shoulder_width.toFixed(1)} cm` : '--';

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.header}>
        <View style={styles.dateWrap}>
          <Text style={styles.dateIcon}>📊</Text>
          <Text style={styles.dateText}>{date}</Text>
        </View>
        {onDelete && (
          <TouchableOpacity onPress={onDelete} style={styles.deleteBtn}>
            <Text style={styles.deleteIcon}>🗑️</Text>
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.metricsRow}>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Arm Length</Text>
          <Text style={styles.metricVal}>{arm}</Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Leg Length</Text>
          <Text style={styles.metricVal}>{leg}</Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Shoulder</Text>
          <Text style={styles.metricVal}>{shoulder}</Text>
        </View>
      </View>

      <View style={styles.footer}>
        <Text style={styles.viewDetailsText}>Tap for full scan report ›</Text>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  dateWrap: { flexDirection: 'row', alignItems: 'center' },
  dateIcon: { fontSize: 16, marginRight: 6 },
  dateText: { color: Colors.accent, fontSize: 14, fontWeight: '700' },
  deleteBtn: { padding: 4 },
  deleteIcon: { fontSize: 14 },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: Colors.primary,
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  metric: { alignItems: 'center', flex: 1 },
  metricLabel: { color: Colors.textSecondary, fontSize: 11, marginBottom: 4 },
  metricVal: { color: Colors.textPrimary, fontSize: 14, fontWeight: '700' },
  footer: { alignItems: 'flex-end', marginTop: 4 },
  viewDetailsText: { color: Colors.textSecondary, fontSize: 12, fontWeight: '500' },
});

export default MeasurementCard;
