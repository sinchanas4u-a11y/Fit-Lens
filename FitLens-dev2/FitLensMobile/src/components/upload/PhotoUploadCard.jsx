import React, { useState } from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors } from '../../constants/colors';
import ZoomableImageModal from '../common/ZoomableImageModal';

const PhotoUploadCard = ({ title, description, imageUri, onSelect, onRemove }) => {
  const [zoomVisible, setZoomVisible] = useState(false);

  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.desc}>{description}</Text>

      {imageUri ? (
        <View style={styles.imagePreviewWrap}>
          <TouchableOpacity activeOpacity={0.8} onPress={() => setZoomVisible(true)} style={{ width: '100%' }}>
            <Image source={{ uri: imageUri }} style={styles.previewImage} resizeMode="contain" />
            <Text style={styles.tapZoomHint}>🔍 Tap image to zoom & inspect</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.removeBtn} onPress={onRemove}>
            <Text style={styles.removeText}>✕ Remove Photo</Text>
          </TouchableOpacity>

          <ZoomableImageModal
            visible={zoomVisible}
            imageSource={{ uri: imageUri }}
            title={title}
            onClose={() => setZoomVisible(false)}
          />
        </View>
      ) : (
        <TouchableOpacity style={styles.uploadArea} onPress={onSelect}>
          <Text style={styles.uploadIcon}>📷</Text>
          <Text style={styles.uploadText}>Select or Capture Photo</Text>
          <Text style={styles.uploadSub}>Tap to open camera or gallery</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  title: { color: Colors.textPrimary, fontSize: 16, fontWeight: '700', marginBottom: 4 },
  desc: { color: Colors.textSecondary, fontSize: 12, marginBottom: 12 },
  uploadArea: {
    height: 140,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: Colors.accent,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.primary + '80',
  },
  uploadIcon: { fontSize: 32, marginBottom: 6 },
  uploadText: { color: Colors.accent, fontSize: 14, fontWeight: '700' },
  uploadSub: { color: Colors.textSecondary, fontSize: 11, marginTop: 2 },
  imagePreviewWrap: { alignItems: 'center' },
  previewImage: { width: '100%', height: 180, borderRadius: 10 },
  tapZoomHint: {
    color: Colors.accent,
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: 4,
  },
  removeBtn: {
    marginTop: 8,
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: '#E53E3E20',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.error,
  },
  removeText: { color: Colors.error, fontSize: 12, fontWeight: '600' },
});

export default PhotoUploadCard;
