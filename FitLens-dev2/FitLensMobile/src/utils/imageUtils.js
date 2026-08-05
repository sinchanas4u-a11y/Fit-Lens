export const formatBase64Image = (b64) => {
  if (!b64) return null;
  if (b64.startsWith('data:image/')) return b64;
  return `data:image/jpeg;base64,${b64}`;
};

export const resizeImageForUpload = async (imageUri) => {
  // Return uri or formatted object for upload
  return {
    uri: imageUri,
    type: 'image/jpeg',
    name: 'photo.jpg',
  };
};
