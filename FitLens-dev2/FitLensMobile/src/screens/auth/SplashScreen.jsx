import React, { useEffect } from 'react';
import { View, Text, StyleSheet, StatusBar } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { Colors } from '../../constants/colors';
import { useAuthStore } from '../../store/authStore';

const SplashScreen = ({ navigation }) => {
  const { isLoggedIn } = useAuthStore();

  useEffect(() => {
    const timer = setTimeout(() => {
      if (!isLoggedIn) {
        navigation.replace('Login');
      }
    }, 2000);
    return () => clearTimeout(timer);
  }, [isLoggedIn]);

  return (
    <LinearGradient colors={Colors.darkGradient} style={styles.container}>
      <StatusBar barStyle="light-content" />
      <View style={styles.center}>
        <Text style={styles.logo}>📏</Text>
        <Text style={styles.title}>FitLens AI</Text>
        <Text style={styles.subtitle}>AI-Powered Body Measurements</Text>
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  center: { alignItems: 'center' },
  logo: { fontSize: 72, marginBottom: 12 },
  title: { fontSize: 36, fontWeight: '800', color: Colors.accent, textAlign: 'center' },
  subtitle: { color: Colors.textSecondary, fontSize: 14, marginTop: 8 },
});

export default SplashScreen;
