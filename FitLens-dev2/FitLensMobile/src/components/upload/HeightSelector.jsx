import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors } from '../../constants/colors';

const HeightSelector = ({ heightCm, onChangeHeightCm }) => {
  const [heightUnit, setHeightUnit] = useState('cm'); // 'cm', 'ft', or 'in'
  const [valCm, setValCm] = useState(heightCm || '165');
  const [valFt, setValFt] = useState('5');
  const [valIn, setValIn] = useState('5');
  const [valInches, setValInches] = useState('65');

  // Calculate current height in cm based on active unit
  const getHeightInCm = () => {
    if (heightUnit === 'cm') {
      const val = parseFloat(valCm);
      if (isNaN(val) || val <= 0) return null;
      return val;
    }
    if (heightUnit === 'ft') {
      const ft = parseFloat(valFt) || 0;
      const inches = parseFloat(valIn) || 0;
      if (ft <= 0 && inches <= 0) return null;
      return (ft * 30.48) + (inches * 2.54);
    }
    if (heightUnit === 'in') {
      const val = parseFloat(valInches);
      if (isNaN(val) || val <= 0) return null;
      return val * 2.54;
    }
    return null;
  };

  useEffect(() => {
    const cm = getHeightInCm();
    if (cm && onChangeHeightCm) {
      onChangeHeightCm(cm.toFixed(1));
    }
  }, [heightUnit, valCm, valFt, valIn, valInches]);

  return (
    <View style={styles.heightCard}>
      <Text style={styles.heightTitle}>📏 Your Height (Required for Scale)</Text>

      {/* 3 unit toggle buttons */}
      <View style={styles.unitRow}>
        {['cm', 'ft', 'in'].map((unit) => (
          <TouchableOpacity
            key={unit}
            onPress={() => setHeightUnit(unit)}
            style={[
              styles.unitBtn,
              heightUnit === unit && styles.unitBtnActive,
            ]}>
            <Text
              style={[
                styles.unitBtnText,
                heightUnit === unit && styles.unitBtnTextActive,
              ]}>
              {unit === 'ft' ? 'FT' : unit === 'in' ? 'IN' : 'CM'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* CM input */}
      {heightUnit === 'cm' && (
        <View style={styles.inputRow}>
          <TextInput
            style={styles.heightInput}
            placeholder="e.g. 165"
            placeholderTextColor="#4A5568"
            value={valCm}
            onChangeText={setValCm}
            keyboardType="numeric"
          />
          <Text style={styles.unitLabel}>cm</Text>
        </View>
      )}

      {/* FT + IN input */}
      {heightUnit === 'ft' && (
        <View style={{ flexDirection: 'row', gap: 8 }}>
          <View style={[styles.inputRow, { flex: 1 }]}>
            <TextInput
              style={[styles.heightInput, { flex: 1 }]}
              placeholder="5"
              placeholderTextColor="#4A5568"
              value={valFt}
              onChangeText={setValFt}
              keyboardType="numeric"
            />
            <Text style={styles.unitLabel}>ft</Text>
          </View>
          <View style={[styles.inputRow, { flex: 1 }]}>
            <TextInput
              style={[styles.heightInput, { flex: 1 }]}
              placeholder="5"
              placeholderTextColor="#4A5568"
              value={valIn}
              onChangeText={setValIn}
              keyboardType="numeric"
            />
            <Text style={styles.unitLabel}>in</Text>
          </View>
        </View>
      )}

      {/* INCHES only input */}
      {heightUnit === 'in' && (
        <View style={styles.inputRow}>
          <TextInput
            style={styles.heightInput}
            placeholder="e.g. 65"
            placeholderTextColor="#4A5568"
            value={valInches}
            onChangeText={setValInches}
            keyboardType="numeric"
          />
          <Text style={styles.unitLabel}>inches</Text>
        </View>
      )}

      {/* Show converted cm value */}
      {getHeightInCm() && (
        <Text style={styles.convertedText}>
          = {getHeightInCm()?.toFixed(1)} cm
        </Text>
      )}

      <Text style={styles.heightNote}>
        Height calibrates pixel-to-cm ratio for precise AI scaling
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  heightCard: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  heightTitle: {
    color: Colors.textPrimary,
    fontWeight: '700',
    fontSize: 15,
    marginBottom: 12,
  },
  unitRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  unitBtn: {
    flex: 1,
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    backgroundColor: Colors.primary,
  },
  unitBtnActive: {
    borderColor: Colors.accent,
    backgroundColor: Colors.accent + '20',
  },
  unitBtnText: {
    color: Colors.textSecondary,
    fontWeight: '600',
    fontSize: 14,
  },
  unitBtnTextActive: { color: Colors.accent },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.primary,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.accent,
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  heightInput: {
    flex: 1,
    color: Colors.textPrimary,
    fontSize: 22,
    fontWeight: '700',
    paddingVertical: 12,
  },
  unitLabel: {
    color: Colors.accent,
    fontWeight: '700',
    fontSize: 16,
  },
  convertedText: {
    color: Colors.accent,
    fontSize: 13,
    marginBottom: 8,
    fontStyle: 'italic',
  },
  heightNote: {
    color: Colors.textSecondary,
    fontSize: 12,
  },
});

export default HeightSelector;
