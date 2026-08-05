import RNFS from 'react-native-fs';
import Share from 'react-native-share';

export const fileService = {
  saveAndShareFile: async (base64Data, filename, mimeType) => {
    try {
      const path = `${RNFS.DocumentDirectoryPath}/${filename}`;
      await RNFS.writeFile(path, base64Data, 'base64');
      await Share.open({
        url: `file://${path}`,
        type: mimeType,
        filename: filename,
      });
      return path;
    } catch (error) {
      console.log('Share error:', error);
      throw error;
    }
  },
};
