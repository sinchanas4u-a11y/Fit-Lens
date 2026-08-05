import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors } from '../../constants/colors';
import { feetInchesToCm, cmToFeetInches } from '../../utils/formatUtils';

const HeightSelector = ({ heightCm, onChangeHeightCm }) => {
  const [unit, setUnit] = useState('cm'); // 'cm' or 'ft'
  const [feet, setFeet] = useState('5');
  const [inches, setInches] = useState('7');

  const handleCmChange = (val) => {
    onChangeHeightCm(val);
    const { feet: f, inches: i } = cmToFeetInches(parseFloat(val));
    setFeet(String(f));
    setInches(String(i));
  };

  const handleFeetInchesChange = (f, i) => {
    setFeet(f);
    setInches(i);
    const cm = feetInchesToCm(f, i);
    onChangeHeightCm(String(cm));
  };

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>Your Height (Required for Scale)</Text>
        <View style={styles.unitToggle}>
          <TouchableOpacity
            style={[styles.unitBtn, unit === 'cm' && styles.unitActive]}
            onPress={() => setUnit('cm')}>
            <Text style={[styles.unitText, unit === 'cm' && styles.unitTextActive]}>CM</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.unitBtn, unit === 'ft' && styles.unitActive]}
            onPress={() => setUnit('ft')}>
            <Text style={[styles.unitText, unit === 'ft' && styles.unitTextActive]}>FT / IN</Text>
          </TouchableOpacity>
        </View>
      </View>

      {unit === 'cm' ? (
        <View style={styles.inputWrap}>
          <TextInput
            style={styles.input}
            value={heightCm}
            onChangeText={handleCmChange}
            keyboardType="numeric"
            placeholder="165"
            placeholderTextColor={Colors.textSecondary}
          />
          <Text style={styles.unitLabel}>cm</Text>
        </View>
      ) : (
        <View style={styles.feetRow}>
          <View style={[styles.inputWrap, { flex: 1, marginRight: 8 }]}>
            <TextInput
              style={styles.input}
              value={feet}
              onChangeText={(f) => handleFeetInchesChange(f, inches)}
              keyboardType="numeric"
              placeholder="5"
              placeholderTextColor={Colors.textSecondary}
            />
            <Text style={styles.unitLabel}>ft</Text>
          </View>
          <View style={[styles.inputWrap, { flex: 1 }]}>
            <TextInput
              style={styles.input}
              value={inches}
              onChangeText={(i) => handleFeetInchesChange(feet, i)}
              keyboardType="numeric"
              placeholder="7"
              placeholderTextColor={Colors.textSecondary}
            />
            <Text style={styles.unitLabel}>in</Text>
          </View>
        </View>
      )}

      <Text style={styles.hint}>Height is used to calibrate pixel-to-cm ratios for precise AI scaling.</Text>
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
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: { color: Colors.textPrimary, fontSize: 14, fontWeight: '700' },
  unitToggle: {
    flexDirection: 'row',
    backgroundColor: Colors.primary,
    borderRadius: 8,
    padding: 2,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  unitBtn: { paddingVertical: 4, paddingHorizontal: 8, borderRadius: 6 },
  unitActive: { backgroundColor: Colors.accent },
  unitText: { color: Colors.textSecondary, fontSize: 11, fontWeight: '700' },
  unitTextActive: { color: Colors.primary },
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.primary,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingHorizontal: 16,
  },
  input: {
    flex: 1,
    color: Colors.textPrimary,
    fontSize: 18,
    fontWeight: '700',
    paddingVertical: 10,
  },
  unitLabel: { color: Colors.textSecondary, fontSize: 14, fontWeight: '600' },
  feetRow: { flexDirection: 'row' },
  hint: { color: Colors.textSecondary, fontSize: 11, marginTop: 8 },
});

export default HeightSelector;
