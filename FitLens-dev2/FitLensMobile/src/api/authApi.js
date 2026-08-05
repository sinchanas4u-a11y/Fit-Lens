import axiosInstance from './axiosInstance';
import { Endpoints } from '../constants/endpoints';

export const authApi = {
  login: (email, password) =>
    axiosInstance.post(Endpoints.LOGIN, { email, password }),

  register: (name, email, password) =>
    axiosInstance.post(Endpoints.REGISTER, { name, email, password }),

  forgotPassword: (email) =>
    axiosInstance.post(Endpoints.FORGOT_PASSWORD, { email }),

  resetPassword: (token, newPassword, confirmPassword) =>
    axiosInstance.post(Endpoints.RESET_PASSWORD, {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword,
    }),

  changePassword: (currentPassword, newPassword, confirmPassword) =>
    axiosInstance.post(Endpoints.CHANGE_PASSWORD, {
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    }),

  getMe: () => axiosInstance.get(Endpoints.ME),

  updateProfile: (name) =>
    axiosInstance.put(Endpoints.UPDATE_PROFILE, { name }),

  deleteAccount: (password) =>
    axiosInstance.delete(Endpoints.DELETE_ACCOUNT, { data: { password } }),

  saveFace: (frontImageBase64) =>
    axiosInstance.post(Endpoints.SAVE_FACE, { front_image: frontImageBase64 }),

  verifyFace: (frontImageBase64) =>
    axiosInstance.post(Endpoints.VERIFY_FACE, { front_image: frontImageBase64 }),
};
