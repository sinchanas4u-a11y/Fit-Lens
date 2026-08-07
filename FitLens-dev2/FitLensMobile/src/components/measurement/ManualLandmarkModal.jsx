import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, Modal, TouchableOpacity,
  Image, Dimensions, PanResponder, Alert, ScrollView
} from 'react-native';
import Svg, { Line, Text as SvgText, G } from 'react-native-svg';
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
  const [pointsMap, setPointsMap] = useState({}); // { [typeId]: [{x, y}, {x, y}] }
  const [draggingPoint, setDraggingPoint] = useState(null); // { typeId, pointIndex }
  const [imgLayout, setImgLayout] = useState({ width: SCREEN_WIDTH - 32, height: 420 });
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

  // Reset points state when modal opens or image changes
  useEffect(() => {
    if (visible) {
      setPointsMap({});
      setSelectedType('shoulder');
      setDraggingPoint(null);
    }
  }, [visible, imageUri]);

  // Total complete marked lines (2 points placed)
  const totalMarked = Object.values(pointsMap).filter(
    (pts) => pts && pts.length === 2
  ).length;

  // Handle tap on image to place points (Uses functional state updater to eliminate stale closures)
  const handleImageTap = (evt) => {
    if (draggingPoint) return;
    const { locationX, locationY } = evt.nativeEvent;

    setPointsMap((prev) => {
      const current = prev[selectedType] || [];
      if (current.length === 0) {
        // Place first point
        return { ...prev, [selectedType]: [{ x: locationX, y: locationY }] };
      } else if (current.length === 1) {
        // Place second point — line complete
        return { ...prev, [selectedType]: [current[0], { x: locationX, y: locationY }] };
      } else {
        // Both points exist — reset and start fresh with first point
        return { ...prev, [selectedType]: [{ x: locationX, y: locationY }] };
      }
    });
  };

  // Create PanResponder for a specific handle point
  const createPointPanResponder = useCallback(
    (typeId, pointIndex) => {
      return PanResponder.create({
        onStartShouldSetPanResponder: () => true,
        onStartShouldSetPanResponderCapture: () => true,
        onMoveShouldSetPanResponder: () => true,
        onMoveShouldSetPanResponderCapture: () => true,

        onPanResponderGrant: (evt) => {
          evt.stopPropagation?.();
          setDraggingPoint({ typeId, pointIndex });
        },

        onPanResponderMove: (evt, gestureState) => {
          setPointsMap((prev) => {
            const current = [...(prev[typeId] || [])];
            if (!current[pointIndex]) return prev;

            const newX = Math.max(
              0,
              Math.min(imgLayout.width, current[pointIndex].x + gestureState.dx)
            );
            const newY = Math.max(
              0,
              Math.min(imgLayout.height, current[pointIndex].y + gestureState.dy)
            );

            const updated = [...current];
            updated[pointIndex] = { x: newX, y: newY };
            return { ...prev, [typeId]: updated };
          });
        },

        onPanResponderRelease: () => {
          setDraggingPoint(null);
        },

        onPanResponderTerminate: () => {
          setDraggingPoint(null);
        },
      });
    },
    [imgLayout]
  );

  const handleClearCurrent = () => {
    setPointsMap((prev) => {
      const copy = { ...prev };
      delete copy[selectedType];
      return copy;
    });
  };

  const handleResetAll = () => {
    setPointsMap({});
    setDraggingPoint(null);
  };

  const handleDone = () => {
    if (totalMarked === 0) {
      Alert.alert('No Points Marked', 'Please mark at least one measurement line before proceeding.');
      return;
    }

    const scaleX = naturalSize.width / (imgLayout.width || 1);
    const scaleY = naturalSize.height / (imgLayout.height || 1);

    const formattedLandmarks = [];
    Object.entries(pointsMap).forEach(([typeId, pts]) => {
      if (pts && pts.length === 2) {
        const activeType = LANDMARK_TYPES.find((t) => t.id === typeId);
        formattedLandmarks.push({
          type: typeId,
          label: activeType?.label || typeId,
          points: pts.map((p) => {
            const imgX = p.x * scaleX;
            const imgY = p.y * scaleY;
            return {
              x: imgX,
              y: imgY,
              x_norm: imgX / (naturalSize.width || 1),
              y_norm: imgY / (naturalSize.height || 1),
            };
          }),
        });
      }
    });

    onComplete({
      imageType,
      imageWidth: naturalSize.width,
      imageHeight: naturalSize.height,
      landmarks: formattedLandmarks,
    });
  };

  const activeTypeObj = LANDMARK_TYPES.find((t) => t.id === selectedType);
  const currentPoints = pointsMap[selectedType] || [];

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
            Select a measurement below, tap 2 points on the image to draw a line, then drag handles to fine-tune.
          </Text>
        </View>

        {/* Type Selector Pills */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillContainer}>
          {LANDMARK_TYPES.map((type) => {
            const isSelected = selectedType === type.id;
            const isDone = pointsMap[type.id]?.length === 2;
            return (
              <TouchableOpacity
                key={type.id}
                onPress={() => setSelectedType(type.id)}
                style={[
                  styles.pill,
                  { borderColor: type.color },
                  isSelected && { backgroundColor: type.color + '33' },
                  isDone && { borderColor: '#48BB78' },
                ]}>
                <Text style={[styles.pillText, { color: isSelected ? type.color : Colors.textSecondary }]}>
                  {isDone ? '✓ ' : ''}{type.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* Active Type Status */}
        <View style={styles.statusRow}>
          <Text style={[styles.statusText, { color: activeTypeObj?.color }]}>
            Current: {activeTypeObj?.label} —{' '}
            {currentPoints.length === 0
              ? 'Tap 1st point'
              : currentPoints.length === 1
              ? 'Tap 2nd point'
              : 'Done! Drag handles to adjust'}
          </Text>
          {currentPoints.length > 0 && (
            <TouchableOpacity onPress={handleClearCurrent}>
              <Text style={styles.clearText}>Clear</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Main Image Viewport Area — NO ScrollView wrapping this */}
        <View
          style={styles.imageViewport}
          onLayout={(e) => {
            const { width, height } = e.nativeEvent.layout;
            setImgLayout({ width, height });
          }}>
          {/* Base Layer: TouchableOpacity for tap detection */}
          <TouchableOpacity
            activeOpacity={1}
            onPress={handleImageTap}
            style={StyleSheet.absoluteFill}>
            {imageUri ? (
              <Image source={{ uri: imageUri }} style={styles.image} resizeMode="contain" />
            ) : (
              <View style={styles.noImgBox}><Text style={{ color: '#fff' }}>No Image</Text></View>
            )}
          </TouchableOpacity>

          {/* Lines Layer: Non-interactive rendering of lines & distance labels */}
          <View style={StyleSheet.absoluteFill} pointerEvents="none">
            <Svg style={StyleSheet.absoluteFill}>
              {Object.entries(pointsMap).map(([typeId, pts]) => {
                if (!pts || pts.length < 2) return null;
                const typeObj = LANDMARK_TYPES.find((t) => t.id === typeId);
                const color = typeObj?.color || '#00D4AA';

                const [p1, p2] = pts;
                const distPx = Math.round(Math.hypot(p2.x - p1.x, p2.y - p1.y));
                const midX = (p1.x + p2.x) / 2;
                const midY = (p1.y + p2.y) / 2;

                return (
                  <G key={`line-${typeId}`}>
                    <Line
                      x1={p1.x} y1={p1.y}
                      x2={p2.x} y2={p2.y}
                      stroke={color}
                      strokeWidth="3"
                    />
                    <SvgText
                      x={midX} y={midY - 8}
                      fill={color}
                      fontSize="12"
                      fontWeight="bold"
                      textAnchor="middle">
                      {typeObj?.label}: {distPx}px
                    </SvgText>
                  </G>
                );
              })}
            </Svg>
          </View>

          {/* Points Layer: Interactive handle circles (pointerEvents="box-none" so parent touches pass to handles) */}
          <View style={StyleSheet.absoluteFill} pointerEvents="box-none">
            {Object.entries(pointsMap).map(([typeId, pts]) => {
              if (!pts) return null;
              const typeObj = LANDMARK_TYPES.find((t) => t.id === typeId);
              const color = typeObj?.color || '#00D4AA';
              const isSelected = selectedType === typeId;

              return pts.map((pt, index) => {
                const panResponder = createPointPanResponder(typeId, index);
                const isDragging =
                  draggingPoint?.typeId === typeId && draggingPoint?.pointIndex === index;

                return (
                  <View
                    key={`point-${typeId}-${index}`}
                    {...panResponder.panHandlers}
                    style={[
                      styles.landmarkHandle,
                      {
                        left: pt.x - 16,
                        top: pt.y - 16,
                        backgroundColor: isDragging
                          ? '#FFD700'
                          : isSelected
                          ? color
                          : 'rgba(160,174,192,0.8)',
                        transform: [{ scale: isDragging ? 1.4 : 1.0 }],
                        zIndex: isDragging ? 999 : 10,
                      },
                    ]}>
                    <Text style={styles.handleText}>
                      {index === 0 ? '1' : '2'}
                    </Text>
                  </View>
                );
              });
            })}
          </View>
        </View>

        {/* Footer Actions */}
        <View style={styles.footer}>
          <TouchableOpacity onPress={handleResetAll} style={styles.resetBtn}>
            <Text style={styles.resetBtnText}>↺ Reset All Points</Text>
          </TouchableOpacity>
          <Text style={styles.countText}>
            Marked: {totalMarked} / {LANDMARK_TYPES.length}
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
  landmarkHandle: {
    position: 'absolute',
    width: 32, height: 32,
    borderRadius: 16,
    borderWidth: 3,
    borderColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.8,
    shadowRadius: 4,
  },
  handleText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
  },
  footer: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', padding: 16, borderTopWidth: 1, borderTopColor: '#1A1F3A',
  },
  resetBtn: { padding: 8 },
  resetBtnText: { color: '#00D4AA', fontSize: 14, fontWeight: '700' },
  countText: { color: '#A0AEC0', fontSize: 14 },
});

export default ManualLandmarkModal;
