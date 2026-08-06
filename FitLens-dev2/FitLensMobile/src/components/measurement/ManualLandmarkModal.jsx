import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, StyleSheet, Modal, TouchableOpacity,
  Image, Dimensions, PanResponder, Alert, ScrollView
} from 'react-native';
import Svg, { Circle, Line, Text as SvgText, G } from 'react-native-svg';
import { Colors } from '../../constants/colors';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const LANDMARK_TYPES = [
  { id: 'shoulder', label: 'Shoulder Width', color: '#FF6B6B', desc: 'Mark left & right shoulder edges' },
  { id: 'chest', label: 'Chest Width', color: '#4ECDC4', desc: 'Mark left & right chest edges' },
  { id: 'waist', label: 'Waist Width', color: '#45B7D1', desc: 'Mark left & right waist edges' },
  { id: 'hip', label: 'Hip Width', color: '#FFA07A', desc: 'Mark left & right hip edges' },
  { id: 'torso', label: 'Torso Length', color: '#9B59B6', desc: 'Mark shoulder to hip' },
  { id: 'arm', label: 'Arm Length', color: '#98D8C8', desc: 'Mark shoulder to wrist' },
  { id: 'leg', label: 'Leg Length', color: '#F7DC6F', desc: 'Mark hip to ankle' },
  { id: 'custom', label: 'Custom', color: '#BB8FCE', desc: 'Mark any two points' },
];

const ManualLandmarkModal = ({
  visible,
  imageUri,
  imageType = 'front',
  onComplete,
  onCancel,
}) => {
  const [selectedType, setSelectedType] = useState('shoulder');
  const [landmarks, setLandmarks] = useState([]);
  const [currentStartPoint, setCurrentStartPoint] = useState(null);
  const [draggingPoint, setDraggingPoint] = useState(null); // { lIdx, pIdx }

  // Image layout dimensions
  const [imgLayout, setImgLayout] = useState({ width: SCREEN_WIDTH - 32, height: 420, x: 0, y: 0 });
  const [naturalSize, setNaturalSize] = useState({ width: 1080, height: 1440 });

  useEffect(() => {
    if (imageUri) {
      Image.getSize(
        imageUri,
        (w, h) => setNaturalSize({ width: w, height: h }),
        (err) => console.log('Image.getSize error:', err)
      );
    }
  }, [imageUri]);

  // Touch Handler using PanResponder
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt) => {
        const { locationX, locationY } = evt.nativeEvent;
        handleTouchStart(locationX, locationY);
      },
      onPanResponderMove: (evt) => {
        const { locationX, locationY } = evt.nativeEvent;
        handleTouchMove(locationX, locationY);
      },
      onPanResponderRelease: () => {
        setDraggingPoint(null);
      },
    })
  ).current;

  const findNearbyPoint = (touchX, touchY, radius = 24) => {
    for (let lIdx = 0; lIdx < landmarks.length; lIdx++) {
      const lm = landmarks[lIdx];
      for (let pIdx = 0; pIdx < lm.points.length; pIdx++) {
        const pt = lm.points[pIdx];
        const dist = Math.hypot(pt.x - touchX, pt.y - touchY);
        if (dist <= radius) {
          return { lIdx, pIdx };
        }
      }
    }
    return null;
  };

  const handleTouchStart = (x, y) => {
    // 1. Check if user tapped near an existing point to drag
    const nearby = findNearbyPoint(x, y);
    if (nearby) {
      setDraggingPoint(nearby);
      return;
    }

    // 2. Otherwise add new point
    if (!currentStartPoint) {
      setCurrentStartPoint({ x, y });
    } else {
      // Finish landmark line
      const activeType = LANDMARK_TYPES.find((t) => t.id === selectedType);
      const newLandmark = {
        type: selectedType,
        label: activeType?.label || 'Custom',
        color: activeType?.color || '#00D4AA',
        points: [currentStartPoint, { x, y }],
      };

      setLandmarks((prev) => [...prev.filter((l) => l.type !== selectedType), newLandmark]);
      setCurrentStartPoint(null);
    }
  };

  const handleTouchMove = (x, y) => {
    if (draggingPoint) {
      const { lIdx, pIdx } = draggingPoint;
      setLandmarks((prev) =>
        prev.map((lm, i) => {
          if (i !== lIdx) return lm;
          const updatedPts = lm.points.map((p, j) => (j === pIdx ? { x, y } : p));
          return { ...lm, points: updatedPts };
        })
      );
    }
  };

  const handleClearCurrent = () => {
    setLandmarks((prev) => prev.filter((l) => l.type !== selectedType));
    setCurrentStartPoint(null);
  };

  const handleResetAll = () => {
    setLandmarks([]);
    setCurrentStartPoint(null);
  };

  const handleDone = () => {
    if (landmarks.length === 0) {
      Alert.alert('No Points Marked', 'Please mark at least one measurement line before proceeding.');
      return;
    }

    // Format landmarks to match Web API structure with normalized coordinates
    const scaleX = naturalSize.width / imgLayout.width;
    const scaleY = naturalSize.height / imgLayout.height;

    const formattedLandmarks = landmarks.map((lm) => ({
      type: lm.type,
      label: lm.label,
      points: lm.points.map((p) => {
        const imgX = p.x * scaleX;
        const imgY = p.y * scaleY;
        return {
          x: imgX,
          y: imgY,
          x_norm: imgX / naturalSize.width,
          y_norm: imgY / naturalSize.height,
        };
      }),
    }));

    onComplete({
      imageType,
      imageWidth: naturalSize.width,
      imageHeight: naturalSize.height,
      landmarks: formattedLandmarks,
    });
  };

  const activeTypeObj = LANDMARK_TYPES.find((t) => t.id === selectedType);

  return (
    <Modal visible={visible} animationType="slide" transparent={false}>
      <View style={styles.container}>

        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onCancel} style={styles.cancelBtn}>
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
          <Text style={styles.title}>
            Manual Marking ({imageType.toUpperCase()})
          </Text>
          <TouchableOpacity onPress={handleDone} style={styles.doneBtn}>
            <Text style={styles.doneText}>Done ✓</Text>
          </TouchableOpacity>
        </View>

        {/* Instructions */}
        <View style={styles.hintBox}>
          <Text style={styles.hintText}>
            Select a measurement below, then tap 2 points on the image to draw a line. Drag points to adjust.
          </Text>
        </View>

        {/* Type Selector Pills */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillContainer}>
          {LANDMARK_TYPES.map((type) => {
            const isSelected = selectedType === type.id;
            const isMarked = landmarks.some((l) => l.type === type.id);
            return (
              <TouchableOpacity
                key={type.id}
                onPress={() => {
                  setSelectedType(type.id);
                  setCurrentStartPoint(null);
                }}
                style={[
                  styles.pill,
                  { borderColor: type.color },
                  isSelected && { backgroundColor: type.color + '33' },
                ]}>
                <Text style={[styles.pillText, { color: isSelected ? type.color : Colors.textSecondary }]}>
                  {isMarked ? '✓ ' : ''}{type.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* Active Type Status */}
        <View style={styles.statusRow}>
          <Text style={[styles.statusText, { color: activeTypeObj?.color }]}>
            Current: {activeTypeObj?.label} — {activeTypeObj?.desc}
          </Text>
          <TouchableOpacity onPress={handleClearCurrent}>
            <Text style={styles.clearText}>Clear Line</Text>
          </TouchableOpacity>
        </View>

        {/* Image & Interactive Touch Overlay */}
        <View
          style={styles.imageViewport}
          onLayout={(e) => setImgLayout(e.nativeEvent.layout)}
          {...panResponder.panHandlers}>
          
          {imageUri ? (
            <Image source={{ uri: imageUri }} style={styles.image} resizeMode="contain" />
          ) : (
            <View style={styles.noImgBox}><Text style={{ color: '#fff' }}>No Image</Text></View>
          )}

          {/* SVG Overlay for Lines & Handle Points */}
          <Svg style={StyleSheet.absoluteFill}>
            {/* Existing Completed Lines */}
            {landmarks.map((lm, idx) => {
              if (lm.points.length < 2) return null;
              const [p1, p2] = lm.points;
              const distPx = Math.round(Math.hypot(p2.x - p1.x, p2.y - p1.y));
              const midX = (p1.x + p2.x) / 2;
              const midY = (p1.y + p2.y) / 2;

              return (
                <G key={idx}>
                  <Line
                    x1={p1.x} y1={p1.y}
                    x2={p2.x} y2={p2.y}
                    stroke={lm.color}
                    strokeWidth="3"
                  />
                  <Circle cx={p1.x} cy={p1.y} r="10" fill={lm.color} stroke="#fff" strokeWidth="2" />
                  <Circle cx={p2.x} cy={p2.y} r="10" fill={lm.color} stroke="#fff" strokeWidth="2" />
                  <SvgText
                    x={midX} y={midY - 8}
                    fill={lm.color}
                    fontSize="13"
                    fontWeight="bold"
                    textAnchor="middle">
                    {lm.label}: {distPx}px
                  </SvgText>
                </G>
              );
            })}

            {/* In-Progress Start Point */}
            {currentStartPoint && (
              <Circle
                cx={currentStartPoint.x}
                cy={currentStartPoint.y}
                r="12"
                fill={activeTypeObj?.color || '#00D4AA'}
                stroke="#fff"
                strokeWidth="3"
              />
            )}
          </Svg>

        </View>

        {/* Footer Actions */}
        <View style={styles.footer}>
          <TouchableOpacity onPress={handleResetAll} style={styles.resetBtn}>
            <Text style={styles.resetBtnText}>🔄 Reset All Points</Text>
          </TouchableOpacity>
          <Text style={styles.countText}>
            Marked: {landmarks.length} / {LANDMARK_TYPES.length}
          </Text>
        </View>

      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0E27', paddingTop: 40 },
  header: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', paddingHorizontal: 16, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: '#1A1F3A',
  },
  cancelBtn: { padding: 8 },
  cancelText: { color: '#FC8181', fontSize: 16, fontWeight: '600' },
  title: { color: '#FFF', fontSize: 16, fontWeight: '700' },
  doneBtn: { backgroundColor: '#00D4AA', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 },
  doneText: { color: '#0A0E27', fontSize: 15, fontWeight: '700' },
  hintBox: { backgroundColor: '#1A1F3A', padding: 10, marginHorizontal: 16, marginTop: 8, borderRadius: 8 },
  hintText: { color: '#A0AEC0', fontSize: 12, textAlign: 'center' },
  pillContainer: { maxHeight: 50, paddingHorizontal: 12, marginVertical: 8 },
  pill: {
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20,
    borderWidth: 1.5, marginRight: 8, justifyContent: 'center',
  },
  pillText: { fontSize: 13, fontWeight: '700' },
  statusRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', paddingHorizontal: 16, marginBottom: 8,
  },
  statusText: { fontSize: 12, fontWeight: '600' },
  clearText: { color: '#FC8181', fontSize: 12, textDecorationLine: 'underline' },
  imageViewport: {
    flex: 1, marginHorizontal: 16, borderRadius: 12,
    overflow: 'hidden', backgroundColor: '#000', position: 'relative',
  },
  image: { width: '100%', height: '100%' },
  noImgBox: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  footer: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', padding: 16, borderTopWidth: 1, borderTopColor: '#1A1F3A',
  },
  resetBtn: { padding: 8 },
  resetBtnText: { color: '#ED8936', fontSize: 14, fontWeight: '600' },
  countText: { color: '#A0AEC0', fontSize: 13 },
});

export default ManualLandmarkModal;
