import axiosInstance from './axiosInstance';
import { Endpoints } from '../constants/endpoints';

export const measurementApi = {
  process: (frontImageBase64, sideImageBase64, userHeight) =>
    axiosInstance.post(Endpoints.PROCESS, {
      front_image: frontImageBase64,
      side_image: sideImageBase64,
      user_height: userHeight,
    }),

  processManual: (requestData) =>
    axiosInstance.post('/api/process-manual', requestData, { timeout: 180000 }),

  validateImage: async (imageUri, view) => {
    const formData = new FormData();
    formData.append('image', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'image.jpg',
    });
    formData.append('view', view);
    return axiosInstance.post(Endpoints.VALIDATE, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  saveMeasurements: (measurements, userHeight, source) =>
    axiosInstance.post(Endpoints.SAVE_MEASUREMENTS, {
      measurements,
      user_height: userHeight,
      source,
    }),

  getHistory: () => axiosInstance.get(Endpoints.HISTORY),

  getLatest: () => axiosInstance.get(Endpoints.LATEST),

  deleteMeasurement: (analysisId) =>
    axiosInstance.delete(`${Endpoints.DELETE_MEASUREMENT}/${analysisId}`),

  downloadReport: (format, measurements) =>
    axiosInstance.post(`/api/download/${format}`, { measurements }, {
      responseType: 'blob',
    }),
};
