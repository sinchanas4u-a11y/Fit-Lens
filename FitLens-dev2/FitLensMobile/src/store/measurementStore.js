import { create } from 'zustand';

export const useMeasurementStore = create((set) => ({
  currentResults: null,
  history: [],
  latestMeasurement: null,
  isProcessing: false,

  setCurrentResults: (results) => set({ currentResults: results }),
  setHistory: (history) => set({ history }),
  setLatest: (latest) => set({ latestMeasurement: latest }),
  setProcessing: (isProcessing) => set({ isProcessing }),
  clearResults: () => set({ currentResults: null }),
}));
