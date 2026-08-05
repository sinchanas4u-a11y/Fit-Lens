import { useState } from 'react';
import { measurementApi } from '../api/measurementApi';
import { useMeasurementStore } from '../store/measurementStore';

export const useMeasurements = () => {
  const [loading, setLoading] = useState(false);
  const {
    currentResults,
    history,
    latestMeasurement,
    setCurrentResults,
    setHistory,
    setLatest,
  } = useMeasurementStore();

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await measurementApi.getHistory();
      if (res.data.history) {
        setHistory(res.data.history);
      }
    } catch (e) {
      console.log('Fetch history error:', e);
    }
    setLoading(false);
  };

  const fetchLatest = async () => {
    try {
      const res = await measurementApi.getLatest();
      if (res.data.latest) {
        setLatest(res.data.latest);
      }
    } catch (e) {}
  };

  const deleteScan = async (analysisId) => {
    try {
      await measurementApi.deleteMeasurement(analysisId);
      setHistory(history.filter((item) => item.analysis_id !== analysisId));
    } catch (e) {
      throw e;
    }
  };

  return {
    loading,
    currentResults,
    history,
    latestMeasurement,
    fetchHistory,
    fetchLatest,
    deleteScan,
    setCurrentResults,
  };
};
