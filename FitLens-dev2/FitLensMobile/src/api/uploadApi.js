import axiosInstance from './axiosInstance';
import { Endpoints } from '../constants/endpoints';

export const uploadApi = {
  uploadAndValidate: async (imageUri, view) => {
    const formData = new FormData();
    formData.append('image', {
      uri: imageUri,
      type: 'image/jpeg',
      name: `${view}_view.jpg`,
    });
    formData.append('view', view);
    return axiosInstance.post(Endpoints.VALIDATE, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  processUpload: (frontImageBase64, sideImageBase64, userHeight) =>
    axiosInstance.post(Endpoints.PROCESS, {
      front_image: frontImageBase64,
      side_image: sideImageBase64,
      user_height: userHeight,
    }),
};
