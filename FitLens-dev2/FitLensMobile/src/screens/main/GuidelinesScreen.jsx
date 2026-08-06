import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Svg, { Circle, Line } from 'react-native-svg';
import Header from '../../components/common/Header';
import Button from '../../components/common/Button';
import { Colors } from '../../constants/colors';

const FrontSilhouette = () => (
  <Svg width="120" height="240" viewBox="0 0 120 240">
    {/* Head */}
    <Circle cx="60" cy="25" r="18" stroke="#00D4AA"
      strokeWidth="2" fill="none" strokeDasharray="4,2"/>
    {/* Neck */}
    <Line x1="60" y1="43" x2="60" y2="58"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
    {/* Shoulders */}
    <Line x1="20" y1="65" x2="100" y2="65"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
    {/* Left arm — angled away A-pose */}
    <Line x1="20" y1="65" x2="5" y2="130"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
    {/* Right arm — angled away A-pose */}
    <Line x1="100" y1="65" x2="115" y2="130"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
    {/* Torso */}
    <Line x1="60" y1="58" x2="60" y2="140"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
    {/* Hips */}
    <Line x1="35" y1="140" x2="85" y2="140"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
    {/* Left leg */}
    <Line x1="42" y1="140" x2="35" y2="225"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
    {/* Right leg */}
    <Line x1="78" y1="140" x2="85" y2="225"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
  </Svg>
);

const SideSilhouette = () => (
  <Svg width="120" height="240" viewBox="0 0 120 240">
    {/* Head side profile */}
    <Circle cx="65" cy="25" r="18" stroke="#00D4AA"
      strokeWidth="2" fill="none" strokeDasharray="4,2"/>
    {/* Neck */}
    <Line x1="65" y1="43" x2="65" y2="58"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
    {/* Torso */}
    <Line x1="65" y1="58" x2="65" y2="140"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
    {/* Arm (one visible from side) */}
    <Line x1="65" y1="70" x2="45" y2="125"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
    {/* Hip */}
    <Line x1="55" y1="140" x2="75" y2="140"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
    {/* Leg (side view — single line) */}
    <Line x1="65" y1="140" x2="65" y2="225"
      stroke="#00D4AA" strokeWidth="2" strokeDasharray="4,2"/>
  </Svg>
);

const GuidelinesScreen = ({ navigation }) => {
  const guidelines = [
    { icon: '🧍', title: 'Stand Straight in A-Pose', desc: 'Arms slightly open away from sides, legs shoulder-width apart.' },
    { icon: '👚', title: 'Fitted Clothing', desc: 'Wear tight-fitting athletic wear or swimsuit for accurate AI silhouette detection.' },
    { icon: '💡', title: 'Good Lighting', desc: 'Ensure plain background and well-lit environment without harsh shadows.' },
    { icon: '📱', title: 'Full Body in Frame', desc: 'Position camera at waist height so head-to-toe is visible.' },
  ];

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <Header title="Photo Guidelines" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.content}>
        {/* Silhouette Preview — Side by Side */}
        <View style={styles.previewCard}>
          <Text style={styles.previewTitle}>Optimal Positioning</Text>

          <View style={{ flexDirection: 'row', justifyContent: 'space-around', alignItems: 'center', padding: 16, width: '100%' }}>
            <View style={{ alignItems: 'center' }}>
              <FrontSilhouette />
              <Text style={{ color: '#00D4AA', marginTop: 8, fontWeight: '700' }}>
                ✅ Front View
              </Text>
              <Text style={{ color: '#A0AEC0', fontSize: 11, textAlign: 'center' }}>
                Face camera directly{'\n'}Arms in A-pose
              </Text>
            </View>
            <View style={{ alignItems: 'center' }}>
              <SideSilhouette />
              <Text style={{ color: '#00D4AA', marginTop: 8, fontWeight: '700' }}>
                ✅ Side View
              </Text>
              <Text style={{ color: '#A0AEC0', fontSize: 11, textAlign: 'center' }}>
                Turn 90° right{'\n'}Arms relaxed
              </Text>
            </View>
          </View>
        </View>

        {/* Guidelines List */}
        <View style={styles.list}>
          {guidelines.map((g, idx) => (
            <View key={idx} style={styles.item}>
              <Text style={styles.itemIcon}>{g.icon}</Text>
              <View style={styles.itemText}>
                <Text style={styles.itemTitle}>{g.title}</Text>
                <Text style={styles.itemDesc}>{g.desc}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Action Buttons */}
        <Button
          title="📸 Proceed to Upload"
          onPress={() => navigation.navigate('Upload')}
          style={{ marginBottom: 12 }}
        />
        <Button
          title="🎥 Use Live Camera"
          variant="secondary"
          onPress={() => navigation.navigate('Camera')}
        />
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 20 },
  previewCard: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 20,
    alignItems: 'center',
  },
  previewTitle: { color: Colors.accent, fontSize: 14, fontWeight: '700', marginBottom: 8 },
  list: { marginBottom: 24 },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.cardBg,
    padding: 16,
    borderRadius: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  itemIcon: { fontSize: 28, marginRight: 16 },
  itemText: { flex: 1 },
  itemTitle: { color: Colors.textPrimary, fontSize: 15, fontWeight: '700', marginBottom: 2 },
  itemDesc: { color: Colors.textSecondary, fontSize: 12, lineHeight: 16 },
});

export default GuidelinesScreen;
