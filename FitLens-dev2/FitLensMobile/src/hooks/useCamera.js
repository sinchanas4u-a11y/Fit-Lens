import { useState } from 'react';
import { cameraService } from '../services/cameraService';

export const useCamera = () => {
  const [loading, setLoading] = useState(false);

  const capturePhoto = async () => {
    setLoading(true);
    try {
      const result = await cameraService.openCamera();
      setLoading(false);
      return result;
    } catch (e) {
      setLoading(false);
      return null;
    }
  };

  const pickGallery = async () => {
    setLoading(true);
    try {
      const result = await cameraService.openGallery();
      setLoading(false);
      return result;
    } catch (e) {
      setLoading(false);
      return null;
    }
  };

  return { capturePhoto, pickGallery, loading };
};
