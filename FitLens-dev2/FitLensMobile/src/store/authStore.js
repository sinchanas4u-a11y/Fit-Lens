import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Config } from '../constants/config';

export const useAuthStore = create((set) => ({
  user: null,
  token: null,
  isLoggedIn: false,
  isLoading: true,

  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),

  login: async (userData, token) => {
    await AsyncStorage.setItem(Config.TOKEN_KEY, token);
    await AsyncStorage.setItem(Config.USER_KEY, JSON.stringify(userData));
    set({ user: userData, token, isLoggedIn: true });
  },

  logout: async () => {
    await AsyncStorage.removeItem(Config.TOKEN_KEY);
    await AsyncStorage.removeItem(Config.USER_KEY);
    set({ user: null, token: null, isLoggedIn: false });
  },

  restoreSession: async () => {
    try {
      const token = await AsyncStorage.getItem(Config.TOKEN_KEY);
      const userStr = await AsyncStorage.getItem(Config.USER_KEY);
      if (token && userStr) {
        set({ token, user: JSON.parse(userStr), isLoggedIn: true });
      }
    } catch (e) {
      console.log('Session restore error:', e);
    }
    set({ isLoading: false });
  },
}));
