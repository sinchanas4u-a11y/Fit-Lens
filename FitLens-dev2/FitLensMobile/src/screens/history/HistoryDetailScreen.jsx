import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Header from '../../components/common/Header';
import MeasurementTable from '../../components/measurement/MeasurementTable';
import Button from '../../components/common/Button';
import { Colors } from '../../constants/colors';

const HistoryDetailScreen = ({ route, navigation }) => {
  const { measurement } = route.params;

  // Reformat flat fields into object mapping for table display if needed
  const extractMeasurementsMap = (item) => {
    if (item.measurements) return item.measurements;
    const map = {};
    const keys = [
      'height_cm',
      'arm_length',
      'leg_length',
      'torso_length',
      'shoulder_width',
      'chest_circumference',
      'waist_circumference',
      'hip_circumference',
      'thigh_circumference',
    ];
    keys.forEach((k) => {
      if (item[k] !== undefined) {
        map[k] = {
          value_cm: item[k],
          source: item.source || 'Historical Scan',
        };
      }
    });
    return map;
  };

  const measureMap = extractMeasurementsMap(measurement);

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <Header title={`Scan — ${measurement.date || 'Detail'}`} onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>📏 Scan Details</Text>
          <Text style={styles.dateSub}>Recorded on {measurement.date || 'Unknown'}</Text>
          <MeasurementTable measurements={measureMap} />
        </View>

        <Button
          title="Back to History"
          variant="secondary"
          onPress={() => navigation.goBack()}
        />
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16, paddingBottom: 40 },
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sectionTitle: { color: Colors.textPrimary, fontSize: 18, fontWeight: '700', marginBottom: 4 },
  dateSub: { color: Colors.textSecondary, fontSize: 12, marginBottom: 16 },
});

export default HistoryDetailScreen;
