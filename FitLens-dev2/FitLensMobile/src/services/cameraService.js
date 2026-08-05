import { launchCamera, launchImageLibrary } from 'react-native-image-picker';
import { uriToBase64 } from '../utils/base64Utils';

const defaultOptions = {
  mediaType: 'photo',
  includeBase64: true,
  maxHeight: 1920,
  maxWidth: 1080,
  quality: 0.85,
};

export const cameraService = {
  openCamera: async () => {
    const result = await launchCamera(defaultOptions);
    if (result.didCancel || result.errorCode) {
      return null;
    }
    const asset = result.assets?.[0];
    if (!asset) return null;
    let b64 = asset.base64;
    if (!b64 && asset.uri) {
      b64 = await uriToBase64(asset.uri);
    }
    return {
      uri: asset.uri,
      base64: b64,
    };
  },

  openGallery: async () => {
    const result = await launchImageLibrary(defaultOptions);
    if (result.didCancel || result.errorCode) {
      return null;
    }
    const asset = result.assets?.[0];
    if (!asset) return null;
    let b64 = asset.base64;
    if (!b64 && asset.uri) {
      b64 = await uriToBase64(asset.uri);
    }
    return {
      uri: asset.uri,
      base64: b64,
    };
  },
};
