import React from 'react';
import { View, StyleSheet, Text } from 'react-native';
import Svg, { Path, Circle } from 'react-native-svg';
import { Colors } from '../../constants/colors';

const SilhouetteOverlay = ({ viewMode = 'front' }) => {
  return (
    <View style={styles.overlay} pointerEvents="none">
      <View style={styles.svgContainer}>
        {viewMode === 'front' ? (
          /* Front view A-pose Silhouette */
          <Svg height="100%" width="100%" viewBox="0 0 200 400">
            {/* Head */}
            <Circle cx="100" cy="50" r="28" stroke={Colors.accent} strokeWidth="2.5" fill="none" strokeDasharray="4,4" />
            {/* Torso & Arms (A-pose) */}
            <Path
              d="M75,80 L125,80 M100,78 L100,210 M100,100 L50,190 M100,100 L150,190 M100,210 L70,360 M100,210 L130,360"
              stroke={Colors.accent}
              strokeWidth="2.5"
              fill="none"
              strokeDasharray="6,4"
            />
          </Svg>
        ) : (
          /* Side view Silhouette */
          <Svg height="100%" width="100%" viewBox="0 0 200 400">
            {/* Head */}
            <Circle cx="100" cy="50" r="26" stroke={Colors.accent} strokeWidth="2.5" fill="none" strokeDasharray="4,4" />
            {/* Side spine line & leg */}
            <Path
              d="M100,76 L95,140 L100,210 M100,210 L95,360"
              stroke={Colors.accent}
              strokeWidth="2.5"
              fill="none"
              strokeDasharray="6,4"
            />
          </Svg>
        )}
      </View>
      <View style={styles.textWrap}>
        <Text style={styles.guideText}>
          {viewMode === 'front' ? 'Align body inside Front A-Pose guide' : 'Turn 90° for Side View guide'}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
  },
  svgContainer: {
    width: '80%',
    height: '75%',
    opacity: 0.8,
  },
  textWrap: {
    position: 'absolute',
    bottom: 90,
    backgroundColor: 'rgba(10, 14, 39, 0.85)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.accent,
  },
  guideText: { color: Colors.accent, fontSize: 13, fontWeight: '700' },
});

export default SilhouetteOverlay;
