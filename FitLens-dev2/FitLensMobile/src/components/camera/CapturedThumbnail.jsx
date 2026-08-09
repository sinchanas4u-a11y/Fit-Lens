import React, { useState } from 'react';
import { View, Image, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors } from '../../constants/colors';
import ZoomableImageModal from '../common/ZoomableImageModal';

const CapturedThumbnail = ({ label, imageUri, onRetake }) => {
  const [zoomVisible, setZoomVisible] = useState(false);

  if (!imageUri) return null;

  return (
    <View style={styles.container}>
      <TouchableOpacity activeOpacity={0.85} onPress={() => setZoomVisible(true)} style={styles.imageWrap}>
        <Image source={{ uri: imageUri }} style={styles.image} resizeMode="cover" />
      </TouchableOpacity>
      <View style={styles.overlay}>
        <Text style={styles.label}>{label}</Text>
        {onRetake && (
          <TouchableOpacity style={styles.retakeBtn} onPress={onRetake}>
            <Text style={styles.retakeText}>Retake</Text>
          </TouchableOpacity>
        )}
      </View>

      <ZoomableImageModal
        visible={zoomVisible}
        imageSource={{ uri: imageUri }}
        title={`Captured ${label}`}
        onClose={() => setZoomVisible(false)}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: 90,
    height: 120,
    borderRadius: 10,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: Colors.accent,
    backgroundColor: Colors.secondary,
  },
  imageWrap: { flex: 1 },
  image: { width: '100%', height: '100%' },
  overlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(10,14,39,0.8)',
    paddingVertical: 4,
    alignItems: 'center',
  },
  label: { color: Colors.accent, fontSize: 10, fontWeight: '700' },
  retakeBtn: { marginTop: 2 },
  retakeText: { color: Colors.error, fontSize: 9, fontWeight: '600' },
});

export default CapturedThumbnail;
