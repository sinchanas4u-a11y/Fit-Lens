import { useAuthStore } from '../store/authStore';
import { authApi } from '../api/authApi';

export const useAuth = () => {
  const { user, token, isLoggedIn, isLoading, login, logout, setUser } = useAuthStore();

  const handleLogin = async (email, password) => {
    const res = await authApi.login(email, password);
    if (res.data.success) {
      await login(res.data.user, res.data.token);
    }
    return res.data;
  };

  const handleRegister = async (name, email, password) => {
    const res = await authApi.register(name, email, password);
    return res.data;
  };

  return {
    user,
    token,
    isLoggedIn,
    isLoading,
    login: handleLogin,
    register: handleRegister,
    logout,
    setUser,
  };
};
