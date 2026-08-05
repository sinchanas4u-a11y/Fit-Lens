import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Header from '../../components/common/Header';
import Button from '../../components/common/Button';
import SilhouetteOverlay from '../../components/camera/SilhouetteOverlay';
import { Colors } from '../../constants/colors';

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
        {/* Silhouette Preview */}
        <View style={styles.previewCard}>
          <Text style={styles.previewTitle}>Optimal Positioning</Text>
          <View style={styles.silhouetteWrap}>
            <SilhouetteOverlay viewMode="front" />
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
  silhouetteWrap: {
    width: '100%',
    height: 180,
    backgroundColor: Colors.primary,
    borderRadius: 12,
    overflow: 'hidden',
  },
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
