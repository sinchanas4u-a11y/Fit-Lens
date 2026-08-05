import { create } from 'zustand';

export const useAppStore = create((set) => ({
  theme: 'dark',
  unitSystem: 'cm', // 'cm' or 'inch'
  isOffline: false,
  activeTab: 'Home',

  setTheme: (theme) => set({ theme }),
  setUnitSystem: (unitSystem) => set({ unitSystem }),
  setIsOffline: (isOffline) => set({ isOffline }),
  setActiveTab: (activeTab) => set({ activeTab }),
}));
