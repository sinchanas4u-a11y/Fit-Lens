import { useState } from 'react';
import { uploadApi } from '../api/uploadApi';

export const useUpload = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const processUpload = async (frontB64, sideB64, heightCm) => {
    setLoading(true);
    setError(null);
    try {
      const res = await uploadApi.processUpload(frontB64, sideB64, parseFloat(heightCm));
      setLoading(false);
      return res.data;
    } catch (e) {
      setLoading(false);
      const msg = e.response?.data?.error || 'Analysis failed. Please try again.';
      setError(msg);
      throw new Error(msg);
    }
  };

  return { processUpload, loading, error };
};
