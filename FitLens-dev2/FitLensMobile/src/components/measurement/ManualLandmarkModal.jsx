import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  View, Text, Image, TouchableOpacity, PanResponder,
  StyleSheet, Dimensions, Modal, ScrollView, Alert
} from 'react-native';
import { Colors } from '../../constants/colors';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const IMAGE_DISPLAY_WIDTH = SCREEN_WIDTH - 32;
const IMAGE_DISPLAY_HEIGHT = SCREEN_HEIGHT * 0.55;

const ManualLandmarkModal = ({
  visible, imageUri, view, imageType, scaleFactor,
  onComplete, onCancel
}) => {
  const activeView = view || imageType || 'front';
  const [scale, setScale] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [points, setPoints] = useState({});
  const [selectedMeasurement, setSelectedMeasurement] = useState('shoulder_width');
  const [isDraggingPoint, setIsDraggingPoint] = useState(null);
  const [isZooming, setIsZooming] = useState(false);

  // Store image container layout:
  const containerLayout = useRef({ x: 0, y: 0, width: IMAGE_DISPLAY_WIDTH, height: IMAGE_DISPLAY_HEIGHT });

  // Store image natural dimensions vs displayed dimensions:
  const imageNaturalSize = useRef({ width: 0, height: 0 });
  const imageDisplayedSize = useRef({ width: IMAGE_DISPLAY_WIDTH, height: IMAGE_DISPLAY_HEIGHT });

  // Reset points and selected measurement when modal opens or view changes
  useEffect(() => {
    if (visible) {
      setPoints({});
      setSelectedMeasurement(activeView === 'front' ? 'shoulder_width' : 'chest_depth');
      scaleRef.current = 1;
      panRef.current = { x: 0, y: 0 };
      setScale(1);
      setPanOffset({ x: 0, y: 0 });
    }
  }, [visible, activeView]);

  // Refs for gesture tracking:
  const scaleRef = useRef(1);
  const panRef = useRef({ x: 0, y: 0 });
  const lastPinchDist = useRef(null);
  const lastPanPos = useRef(null);
  const touchCountRef = useRef(0);

  const measurements = activeView === 'front'
    ? ['shoulder_width', 'chest_width', 'waist_width', 'hip_width']
    : ['chest_depth', 'waist_depth', 'hip_depth', 'stomach_depth'];

  const labels = {
    shoulder_width: 'Shoulder', chest_width: 'Chest',
    waist_width: 'Waist', hip_width: 'Hip',
    chest_depth: 'Chest D', waist_depth: 'Waist D',
    hip_depth: 'Hip D', stomach_depth: 'Stomach D',
  };

  // Calculate displayed image size accounting for resizeMode="contain":
  const calcDisplayedImageSize = (containerW, containerH, imgW, imgH) => {
    if (!containerW || !containerH || !imgW || !imgH) {
      return { width: containerW || IMAGE_DISPLAY_WIDTH, height: containerH || IMAGE_DISPLAY_HEIGHT };
    }
    const containerRatio = containerW / containerH;
    const imageRatio = imgW / imgH;
    let displayW, displayH;
    if (imageRatio > containerRatio) {
      displayW = containerW;
      displayH = containerW / imageRatio;
    } else {
      displayH = containerH;
      displayW = containerH * imageRatio;
    }
    return { width: displayW, height: displayH };
  };

  // Get image natural size on load:
  const handleImageLoad = (e) => {
    if (!e?.nativeEvent?.source) return;
    const { width, height } = e.nativeEvent.source;
    imageNaturalSize.current = { width, height };
    const container = containerLayout.current;
    if (container.width > 0 && container.height > 0) {
      imageDisplayedSize.current = calcDisplayedImageSize(
        container.width, container.height,
        width, height
      );
    }
    console.log('[Image] Natural size:', width, height, 'Displayed:', imageDisplayedSize.current);
  };

  // Get container layout:
  const handleContainerLayout = (e) => {
    const { x, y, width, height } = e.nativeEvent.layout;
    containerLayout.current = { x, y, width, height };
    if (imageNaturalSize.current.width > 0) {
      imageDisplayedSize.current = calcDisplayedImageSize(
        width, height,
        imageNaturalSize.current.width,
        imageNaturalSize.current.height
      );
    }
    console.log('[Container] Layout:', { x, y, width, height });
  };

  // CORRECT coordinate transformation from screen tap to image space:
  const screenToImageCoords = (tapX, tapY) => {
    const container = containerLayout.current;
    const displayed = imageDisplayedSize.current;
    const currentScale = scaleRef.current;
    const currentPan = panRef.current;

    // The image is centered in container with contain mode:
    const imageOffsetX = (container.width - displayed.width) / 2;
    const imageOffsetY = (container.height - displayed.height) / 2;

    // The transform applies scale from CENTER of container:
    const centerX = container.width / 2;
    const centerY = container.height / 2;

    // Reverse the pan offset:
    const unpannedX = tapX - currentPan.x;
    const unpannedY = tapY - currentPan.y;

    // Reverse the scale (scale is from center):
    const unscaledX = centerX + (unpannedX - centerX) / currentScale;
    const unscaledY = centerY + (unpannedY - centerY) / currentScale;

    // Convert to image coordinate (remove image offset within container):
    const imgX = unscaledX - imageOffsetX;
    const imgY = unscaledY - imageOffsetY;

    // Normalize to displayed image bounds:
    return {
      x: Math.max(0, Math.min(displayed.width, imgX)),
      y: Math.max(0, Math.min(displayed.height, imgY)),
    };
  };

  // Reverse transformation for rendering points and lines:
  const imageCoordsToScreen = (imgX, imgY) => {
    const container = containerLayout.current;
    const displayed = imageDisplayedSize.current;
    const currentScale = scaleRef.current;
    const currentPan = panRef.current;

    const imageOffsetX = (container.width - displayed.width) / 2;
    const imageOffsetY = (container.height - displayed.height) / 2;
    const centerX = container.width / 2;
    const centerY = container.height / 2;

    // Add image offset:
    const containerX = imgX + imageOffsetX;
    const containerY = imgY + imageOffsetY;

    // Apply scale from center:
    const scaledX = centerX + (containerX - centerX) * currentScale;
    const scaledY = centerY + (containerY - centerY) * currentScale;

    // Apply pan:
    return {
      x: scaledX + currentPan.x,
      y: scaledY + currentPan.y,
    };
  };

  // Main gesture handler for the image container:
  const containerPanResponder = useRef(PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onMoveShouldSetPanResponder: () => true,
    onStartShouldSetPanResponderCapture: () => false,
    onMoveShouldSetPanResponderCapture: (evt) => {
      // Capture multi-touch for pinch zoom:
      return evt.nativeEvent.touches.length >= 2;
    },

    onPanResponderGrant: (evt) => {
      touchCountRef.current = evt.nativeEvent.touches.length;
      lastPinchDist.current = null;
      lastPanPos.current = null;
    },

    onPanResponderMove: (evt, gesture) => {
      const touches = evt.nativeEvent.touches;
      touchCountRef.current = touches.length;

      if (touches.length === 2) {
        // PINCH TO ZOOM:
        setIsZooming(true);
        const dx = touches[0].pageX - touches[1].pageX;
        const dy = touches[0].pageY - touches[1].pageY;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (lastPinchDist.current) {
          const delta = dist / lastPinchDist.current;
          const newScale = Math.min(Math.max(scaleRef.current * delta, 1), 4);
          scaleRef.current = newScale;
          setScale(newScale);
        }
        lastPinchDist.current = dist;

      } else if (touches.length === 1 && scaleRef.current > 1) {
        // PAN when zoomed in (single finger):
        const touch = touches[0];
        if (lastPanPos.current) {
          const dx = touch.pageX - lastPanPos.current.x;
          const dy = touch.pageY - lastPanPos.current.y;
          const newX = panRef.current.x + dx;
          const newY = panRef.current.y + dy;

          // Clamp pan to prevent going out of bounds:
          const maxPanX = (scaleRef.current - 1) * IMAGE_DISPLAY_WIDTH / 2;
          const maxPanY = (scaleRef.current - 1) * IMAGE_DISPLAY_HEIGHT / 2;
          panRef.current = {
            x: Math.max(-maxPanX, Math.min(maxPanX, newX)),
            y: Math.max(-maxPanY, Math.min(maxPanY, newY)),
          };
          setPanOffset({ ...panRef.current });
        }
        lastPanPos.current = { x: touch.pageX, y: touch.pageY };
      }
    },

    onPanResponderRelease: () => {
      lastPinchDist.current = null;
      lastPanPos.current = null;
      setTimeout(() => setIsZooming(false), 100);
    },
  })).current;

  // Handle tap on image to place landmark points:
  const handleImageTap = useCallback((evt) => {
    if (isZooming || touchCountRef.current > 1) return;

    const { locationX, locationY } = evt.nativeEvent;
    console.log('[Tap] Raw tap location:', locationX, locationY);

    // Convert tap position using exact center-scale and pan transformation:
    const imgCoords = screenToImageCoords(locationX, locationY);
    console.log('[Tap] Image coords:', imgCoords);

    setPoints(prev => {
      const current = prev[selectedMeasurement] || [];
      if (current.length < 2) {
        return { ...prev, [selectedMeasurement]: [...current, imgCoords] };
      } else {
        // Reset and start fresh for this measurement:
        return { ...prev, [selectedMeasurement]: [imgCoords] };
      }
    });
  }, [selectedMeasurement, isZooming]);

  // Create PanResponder for individual draggable points:
  const createPointResponder = useCallback((measurement, index) => {
    return PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onStartShouldSetPanResponderCapture: () => true,
      onMoveShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponderCapture: () => true,

      onPanResponderGrant: () => {
        setIsDraggingPoint({ measurement, index });
      },

      onPanResponderMove: (evt, gesture) => {
        // Convert drag delta from screen space to image space:
        const dxImage = gesture.dx / scaleRef.current;
        const dyImage = gesture.dy / scaleRef.current;

        setPoints(prev => {
          const pts = [...(prev[measurement] || [])];
          if (!pts[index]) return prev;
          const displayed = imageDisplayedSize.current;
          pts[index] = {
            x: Math.max(0, Math.min(displayed.width, pts[index].x + dxImage)),
            y: Math.max(0, Math.min(displayed.height, pts[index].y + dyImage)),
          };
          return { ...prev, [measurement]: pts };
        });
      },

      onPanResponderRelease: () => {
        setIsDraggingPoint(null);
      },
    });
  }, []);

  // Calculate measurement from two points:
  const calcMeasurement = (pts) => {
    if (!pts || pts.length < 2) return null;
    const dx = pts[1].x - pts[0].x;
    const dy = pts[1].y - pts[0].y;
    const px = Math.sqrt(dx * dx + dy * dy);
    return (px * (scaleFactor || 0.19)).toFixed(1);
  };

  // Render measurement line between two points:
  const renderLine = (measurement, pts) => {
    if (!pts || pts.length < 2) return null;
    const p1 = imageCoordsToScreen(pts[0].x, pts[0].y);
    const p2 = imageCoordsToScreen(pts[1].x, pts[1].y);
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx) * (180 / Math.PI);
    const isSelected = selectedMeasurement === measurement;
    const cm = calcMeasurement(pts);

    return (
      <View key={`line-${measurement}`}
        style={{
          position: 'absolute',
          left: p1.x, top: p1.y - 1,
          width: length, height: 3,
          backgroundColor: isSelected ? '#00D4AA' : '#A0AEC0',
          transform: [{ rotate: `${angle}deg` }],
          transformOrigin: 'left center',
        }}
        pointerEvents="none">
        {/* Measurement label at midpoint */}
        <View style={{
          position: 'absolute',
          left: length / 2 - 28, top: -20,
          backgroundColor: 'rgba(0,0,0,0.85)',
          borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2,
          borderWidth: 1, borderColor: '#00D4AA',
        }}>
          <Text style={{ color: '#00D4AA', fontSize: 9, fontWeight: '700' }}>
            {labels[measurement]}: {cm}cm
          </Text>
        </View>
      </View>
    );
  };

  // Render draggable landmark point:
  const renderPoint = (measurement, pt, index) => {
    const screenPos = imageCoordsToScreen(pt.x, pt.y);
    const pointResponder = createPointResponder(measurement, index);
    const isSelected = selectedMeasurement === measurement;
    const isDragging = isDraggingPoint?.measurement === measurement
      && isDraggingPoint?.index === index;

    return (
      <View
        key={`point-${measurement}-${index}`}
        {...pointResponder.panHandlers}
        style={{
          position: 'absolute',
          left: screenPos.x - 14,
          top: screenPos.y - 14,
          width: 28, height: 28, borderRadius: 14,
          backgroundColor: isDragging ? '#FFD700'
            : isSelected ? '#00D4AA' : '#A0AEC0',
          borderWidth: 2, borderColor: '#FFFFFF',
          justifyContent: 'center', alignItems: 'center',
          elevation: isDragging ? 20 : 10,
          zIndex: isDragging ? 999 : 10,
        }}>
        <Text style={{ color: '#fff', fontSize: 10, fontWeight: '900' }}>
          {index === 0 ? 'L' : 'R'}
        </Text>
      </View>
    );
  };

  const handleDone = () => {
    const result = {};
    Object.entries(points).forEach(([key, pts]) => {
      if (pts?.length === 2) {
        const dx = pts[1].x - pts[0].x;
        const dy = pts[1].y - pts[0].y;
        const px = Math.sqrt(dx * dx + dy * dy);
        result[key] = {
          value_cm: parseFloat((px * (scaleFactor || 0.19)).toFixed(1)),
          value_px: parseFloat(px.toFixed(2)),
          source: 'Manual Marking',
        };
      }
    });

    if (Object.keys(result).length === 0) {
      Alert.alert('No Measurements', 'Mark at least one measurement.');
      return;
    }
    onComplete(result);
  };

  const resetZoom = () => {
    scaleRef.current = 1;
    panRef.current = { x: 0, y: 0 };
    setScale(1);
    setPanOffset({ x: 0, y: 0 });
  };

  const totalMarked = Object.values(points)
    .filter(pts => pts?.length === 2).length;

  return (
    <Modal visible={visible} animationType="slide" statusBarTranslucent>
      <View style={styles.container}>

        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onCancel}>
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
          <Text style={styles.title}>
            Mark ({activeView.toUpperCase()})
          </Text>
          <TouchableOpacity onPress={handleDone} style={styles.doneBtn}>
            <Text style={styles.doneBtnText}>Done ✓</Text>
          </TouchableOpacity>
        </View>

        {/* Zoom indicator + reset */}
        <View style={styles.zoomBar}>
          <Text style={styles.zoomText}>
            🔍 {Math.round(scale * 100)}%
          </Text>
          {scale > 1 && (
            <TouchableOpacity onPress={resetZoom} style={styles.resetZoomBtn}>
              <Text style={styles.resetZoomText}>Reset Zoom</Text>
            </TouchableOpacity>
          )}
          <Text style={styles.zoomHint}>
            {scale === 1
              ? 'Pinch to zoom • Tap to place points'
              : 'Drag 1 finger to pan • Tap to place points'}
          </Text>
        </View>

        {/* Measurement selector */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false}
          style={styles.selectorScroll}
          contentContainerStyle={styles.selectorContent}>
          {measurements.map(m => (
            <TouchableOpacity
              key={m}
              onPress={() => setSelectedMeasurement(m)}
              style={[styles.selectorBtn,
                selectedMeasurement === m && styles.selectorBtnActive,
                points[m]?.length === 2 && styles.selectorBtnDone]}>
              <Text style={[styles.selectorText,
                selectedMeasurement === m && { color: '#00D4AA' }]}>
                {labels[m]}
                {points[m]?.length === 2 ? ' ✓' : ''}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Status */}
        <View style={styles.statusBar}>
          <Text style={styles.statusText}>
            {labels[selectedMeasurement]}:{' '}
            {!points[selectedMeasurement]?.length
              ? 'Tap left point'
              : points[selectedMeasurement]?.length === 1
              ? 'Tap right point'
              : `✓ ${calcMeasurement(points[selectedMeasurement])}cm — Drag to adjust`}
          </Text>
          {points[selectedMeasurement]?.length > 0 && (
            <TouchableOpacity onPress={() =>
              setPoints(prev => ({ ...prev, [selectedMeasurement]: [] }))}>
              <Text style={styles.clearText}>Clear</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Image container with zoom + landmarks */}
        <View
          style={styles.imageContainer}
          onLayout={handleContainerLayout}
          {...containerPanResponder.panHandlers}>

          {/* Tappable area for placing points */}
          <TouchableOpacity
            activeOpacity={1}
            onPress={handleImageTap}
            style={StyleSheet.absoluteFill}>
            <Image
              source={{ uri: imageUri }}
              style={{
                width: '100%',
                height: '100%',
                transform: [
                  { scale },
                  { translateX: panOffset.x / scale },
                  { translateY: panOffset.y / scale },
                ],
              }}
              resizeMode="contain"
              onLoad={handleImageLoad}
            />
          </TouchableOpacity>

          {/* Lines — non-interactive layer */}
          <View style={StyleSheet.absoluteFill} pointerEvents="none">
            {Object.entries(points).map(([m, pts]) =>
              renderLine(m, pts)
            )}
          </View>

          {/* Points — interactive layer (rendered LAST to capture touches) */}
          <View style={StyleSheet.absoluteFill} pointerEvents="box-none">
            {Object.entries(points).map(([m, pts]) =>
              pts?.map((pt, i) => renderPoint(m, pt, i))
            )}
          </View>
        </View>

        {/* Bottom bar */}
        <View style={styles.bottomBar}>
          <TouchableOpacity onPress={() => setPoints({})}>
            <Text style={styles.resetText}>↺ Reset All</Text>
          </TouchableOpacity>
          <Text style={styles.markedCount}>
            Marked: {totalMarked}/{measurements.length}
          </Text>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0E27' },
  header: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', padding: 16, paddingTop: 52,
    backgroundColor: '#1A1F3A',
    borderBottomWidth: 1, borderBottomColor: '#2D3561',
  },
  cancelText: { color: '#FC8181', fontWeight: '700', fontSize: 15 },
  title: { color: '#fff', fontWeight: '700', fontSize: 16 },
  doneBtn: {
    backgroundColor: '#00D4AA', borderRadius: 8,
    paddingHorizontal: 14, paddingVertical: 7,
  },
  doneBtnText: { color: '#fff', fontWeight: '700' },
  zoomBar: {
    flexDirection: 'row', alignItems: 'center',
    padding: 8, paddingHorizontal: 16,
    backgroundColor: '#1E2340', gap: 10,
  },
  zoomText: { color: '#00D4AA', fontWeight: '700', fontSize: 13 },
  resetZoomBtn: {
    backgroundColor: '#2D3561', borderRadius: 6,
    paddingHorizontal: 8, paddingVertical: 4,
  },
  resetZoomText: { color: '#00D4AA', fontSize: 11 },
  zoomHint: { color: '#A0AEC0', fontSize: 11, flex: 1, textAlign: 'right' },
  selectorScroll: { maxHeight: 48 },
  selectorContent: { padding: 8, gap: 6 },
  selectorBtn: {
    paddingHorizontal: 12, paddingVertical: 8,
    borderRadius: 20, borderWidth: 1.5,
    borderColor: '#2D3561', backgroundColor: '#1E2340',
  },
  selectorBtnActive: { borderColor: '#00D4AA', backgroundColor: '#00D4AA20' },
  selectorBtnDone: { borderColor: '#48BB78' },
  selectorText: { color: '#A0AEC0', fontSize: 12, fontWeight: '600' },
  statusBar: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', paddingHorizontal: 16, paddingVertical: 6,
    backgroundColor: '#1A1F3A',
  },
  statusText: { color: '#FC8181', fontSize: 12, fontWeight: '600', flex: 1 },
  clearText: { color: '#00D4AA', fontWeight: '700', fontSize: 13 },
  imageContainer: {
    flex: 1, margin: 8,
    borderRadius: 12, overflow: 'hidden',
    borderWidth: 1, borderColor: '#2D3561',
    backgroundColor: '#0A0E27',
    width: IMAGE_DISPLAY_WIDTH,
    height: IMAGE_DISPLAY_HEIGHT,
  },
  bottomBar: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', padding: 16,
    backgroundColor: '#1A1F3A',
    borderTopWidth: 1, borderTopColor: '#2D3561',
  },
  resetText: { color: '#00D4AA', fontWeight: '700' },
  markedCount: { color: '#A0AEC0', fontSize: 14 },
});

export default ManualLandmarkModal;
