import { authApi } from '../api/authApi';
import { storageService } from './storageService';

export const authService = {
  login: async (email, password) => {
    const res = await authApi.login(email, password);
    if (res.data.success) {
      await storageService.setToken(res.data.token);
      await storageService.setUser(res.data.user);
    }
    return res.data;
  },

  register: async (name, email, password) => {
    const res = await authApi.register(name, email, password);
    return res.data;
  },

  logout: async () => {
    await storageService.clearAll();
  },
};
