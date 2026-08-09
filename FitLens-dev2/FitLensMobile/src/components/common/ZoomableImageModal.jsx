import React, { useState, useRef } from 'react';
import {
  Modal,
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  Dimensions,
  Animated,
  PanResponder,
} from 'react-native';
import { Colors } from '../../constants/colors';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

const ZoomableImageModal = ({ visible, onClose, imageSource, title }) => {
  const [scale, setScale] = useState(1);
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const panAnim = useRef(new Animated.ValueXY({ x: 0, y: 0 })).current;

  const lastTapRef = useRef(0);
  const currentScaleRef = useRef(1);

  const resetZoom = () => {
    currentScaleRef.current = 1;
    setScale(1);
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true }),
      Animated.spring(panAnim, { toValue: { x: 0, y: 0 }, useNativeDriver: true }),
    ]).start();
  };

  const handleClose = () => {
    resetZoom();
    onClose();
  };

  const handleDoubleTap = () => {
    const now = Date.now();
    if (now - lastTapRef.current < 300) {
      // Double tap detected
      if (currentScaleRef.current > 1) {
        // Zoom out
        currentScaleRef.current = 1;
        setScale(1);
        Animated.parallel([
          Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true }),
          Animated.spring(panAnim, { toValue: { x: 0, y: 0 }, useNativeDriver: true }),
        ]).start();
      } else {
        // Zoom in to 2.5x
        currentScaleRef.current = 2.5;
        setScale(2.5);
        Animated.spring(scaleAnim, { toValue: 2.5, useNativeDriver: true }).start();
      }
    }
    lastTapRef.current = now;
  };

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: (_, gestureState) => {
        return currentScaleRef.current > 1 || Math.abs(gestureState.dx) > 5 || Math.abs(gestureState.dy) > 5;
      },
      onPanResponderGrant: () => {
        panAnim.setOffset({
          x: panAnim.x._value,
          y: panAnim.y._value,
        });
        panAnim.setValue({ x: 0, y: 0 });
      },
      onPanResponderMove: Animated.event([null, { dx: panAnim.x, dy: panAnim.y }], {
        useNativeDriver: false,
      }),
      onPanResponderRelease: () => {
        panAnim.flattenOffset();
        if (currentScaleRef.current <= 1) {
          Animated.spring(panAnim, { toValue: { x: 0, y: 0 }, useNativeDriver: true }).start();
        }
      },
    })
  ).current;

  if (!visible || !imageSource) return null;

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={handleClose}>
      <StatusBar barStyle="light-content" backgroundColor="#050714" />
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title} numberOfLines={1}>
            {title || 'Image Inspection'}
          </Text>
          <TouchableOpacity onPress={handleClose} style={styles.closeButton} activeOpacity={0.7}>
            <Text style={styles.closeText}>✕</Text>
          </TouchableOpacity>
        </View>

        {/* Content Viewer Area */}
        <TouchableOpacity
          activeOpacity={1}
          onPress={handleDoubleTap}
          style={styles.viewerArea}
        >
          <Animated.View
            {...panResponder.panHandlers}
            style={[
              styles.imageContainer,
              {
                transform: [
                  { scale: scaleAnim },
                  { translateX: panAnim.x },
                  { translateY: panAnim.y },
                ],
              },
            ]}
          >
            <Image source={imageSource} style={styles.image} resizeMode="contain" />
          </Animated.View>
        </TouchableOpacity>

        {/* Footer Hint */}
        <View style={styles.footer}>
          <Text style={styles.hintText}>
            💡 Pinch or Double-Tap to zoom • Drag to pan • Tap ✕ to close
          </Text>
        </View>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050714',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
    backgroundColor: 'rgba(10, 14, 39, 0.95)',
    zIndex: 10,
  },
  title: {
    color: '#00D4AA',
    fontSize: 16,
    fontWeight: '700',
    flex: 1,
    marginRight: 12,
  },
  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '800',
  },
  viewerArea: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  imageContainer: {
    width: SCREEN_WIDTH,
    height: SCREEN_HEIGHT * 0.75,
    alignItems: 'center',
    justifyContent: 'center',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  footer: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(10, 14, 39, 0.95)',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  hintText: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 12,
    fontWeight: '500',
  },
});

export default ZoomableImageModal;
