import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Config } from '../constants/config';

const axiosInstance = axios.create({
  baseURL: Config.BASE_URL,
  timeout: Config.TIMEOUT,
  headers: { 'Content-Type': 'application/json' },
});

// Add JWT token to every request
axiosInstance.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem(Config.TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors globally
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await AsyncStorage.removeItem(Config.TOKEN_KEY);
      await AsyncStorage.removeItem(Config.USER_KEY);
    }
    return Promise.reject(error);
  }
);

// Test connection on startup
export const testConnection = async () => {
  try {
    const res = await axios.get(`${Config.BASE_URL}/api/health`, { timeout: 5000 });
    console.log('✅ Backend connected:', res.data);
    return true;
  } catch (e) {
    console.log('❌ Backend connection failed:', e.message);
    console.log('Check: 1) Flask running? 2) Same WiFi? 3) IP correct?');
    return false;
  }
};

export default axiosInstance;
