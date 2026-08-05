import AsyncStorage from '@react-native-async-storage/async-storage';
import { Config } from '../constants/config';

export const storageService = {
  getToken: () => AsyncStorage.getItem(Config.TOKEN_KEY),
  setToken: (token) => AsyncStorage.setItem(Config.TOKEN_KEY, token),
  removeToken: () => AsyncStorage.removeItem(Config.TOKEN_KEY),

  getUser: async () => {
    const userStr = await AsyncStorage.getItem(Config.USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  },
  setUser: (user) => AsyncStorage.setItem(Config.USER_KEY, JSON.stringify(user)),
  removeUser: () => AsyncStorage.removeItem(Config.USER_KEY),

  clearAll: () => AsyncStorage.clear(),
};
