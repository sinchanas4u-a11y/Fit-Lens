import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Header from '../../components/common/Header';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/authApi';
import { Colors } from '../../constants/colors';

const DeleteAccountScreen = ({ navigation }) => {
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { logout } = useAuthStore();

  const handleDelete = () => {
    if (!password) {
      Alert.alert('Required', 'Please enter your password to confirm deletion');
      return;
    }

    Alert.alert(
      'Permanent Action',
      'Are you absolutely sure you want to delete your FitLens account? All measurements and face profile data will be permanently removed.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Permanently Delete',
          style: 'destructive',
          onPress: async () => {
            setLoading(true);
            try {
              const res = await authApi.deleteAccount(password);
              if (res.data.success) {
                Alert.alert('Account Deleted', 'Your account has been deleted.');
                await logout();
              }
            } catch (e) {
              Alert.alert('Deletion Failed', e.response?.data?.error || 'Could not delete account');
            }
            setLoading(false);
          },
        },
      ]
    );
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <Header title="Delete Account" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <Text style={styles.icon}>⚠️</Text>
          <Text style={styles.title}>Delete FitLens Account</Text>
          <Text style={styles.desc}>
            This action is irreversible. All your profile information, historical scan records, and saved face verification embeddings will be permanently erased.
          </Text>

          <Input
            label="Confirm Your Password"
            placeholder="Enter password to confirm"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          <Button
            title={loading ? 'Deleting...' : 'Delete Account Permanently'}
            variant="danger"
            onPress={handleDelete}
            loading={loading}
            style={{ marginTop: 12 }}
          />
        </View>
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16 },
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
  },
  icon: { fontSize: 48, marginBottom: 12 },
  title: { color: Colors.error, fontSize: 20, fontWeight: '700', marginBottom: 8 },
  desc: { color: Colors.textSecondary, fontSize: 13, textAlign: 'center', marginBottom: 24, lineHeight: 18 },
});

export default DeleteAccountScreen;
