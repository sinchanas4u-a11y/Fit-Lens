import React, { useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl, Alert } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Header from '../../components/common/Header';
import MeasurementCard from '../../components/measurement/MeasurementCard';
import Loader from '../../components/common/Loader';
import { useMeasurements } from '../../hooks/useMeasurements';
import { Colors } from '../../constants/colors';

const HistoryScreen = ({ navigation }) => {
  const { history, loading, fetchHistory, deleteScan } = useMeasurements();

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = (analysisId) => {
    Alert.alert('Confirm Delete', 'Are you sure you want to delete this scan from history?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteScan(analysisId);
          } catch (e) {
            Alert.alert('Error', 'Could not delete measurement scan');
          }
        },
      },
    ]);
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <Header title="Scan History" />

      {loading && history.length === 0 ? (
        <Loader message="Loading your scan history..." />
      ) : (
        <FlatList
          data={history}
          keyExtractor={(item, index) => item.analysis_id || String(index)}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={loading}
              onRefresh={fetchHistory}
              tintColor={Colors.accent}
            />
          }
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={{ fontSize: 48, marginBottom: 12 }}>📊</Text>
              <Text style={styles.emptyTitle}>No Scans Saved Yet</Text>
              <Text style={styles.emptySub}>Your body measurement scans will be saved here automatically.</Text>
            </View>
          }
          renderItem={({ item }) => (
            <MeasurementCard
              item={item}
              onPress={() => navigation.navigate('HistoryDetail', { measurement: item })}
              onDelete={() => handleDelete(item.analysis_id)}
            />
          )}
        />
      )}
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  list: { padding: 16, paddingBottom: 40 },
  empty: { alignItems: 'center', justifyContent: 'center', paddingTop: 80, paddingHorizontal: 32 },
  emptyTitle: { color: Colors.textPrimary, fontSize: 18, fontWeight: '700', marginBottom: 8 },
  emptySub: { color: Colors.textSecondary, fontSize: 13, textAlign: 'center', lineHeight: 18 },
});

export default HistoryScreen;
