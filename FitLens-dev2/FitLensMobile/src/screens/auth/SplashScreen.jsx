import React, { useEffect } from 'react';
import { View, Text, StyleSheet, StatusBar, Image } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { Colors } from '../../constants/colors';
import { useAuthStore } from '../../store/authStore';

const brandLogo = require('../../assets/logo.png');

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
        <Image source={brandLogo} style={styles.logoImage} resizeMode="contain" />
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  center: { alignItems: 'center', paddingHorizontal: 20 },
  logoImage: { width: 280, height: 280, marginBottom: 16 },
});

export default SplashScreen;
