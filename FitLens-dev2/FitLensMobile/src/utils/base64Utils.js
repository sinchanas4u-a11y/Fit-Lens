import RNFS from 'react-native-fs';

export const uriToBase64 = async (uri) => {
  try {
    if (!uri) return '';
    const cleanUri = uri.replace('file://', '');
    const base64Data = await RNFS.readFile(cleanUri, 'base64');
    return base64Data;
  } catch (err) {
    console.error('Error converting URI to base64:', err);
    throw err;
  }
};
