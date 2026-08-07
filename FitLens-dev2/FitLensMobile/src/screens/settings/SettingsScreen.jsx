import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert, Image } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Header from '../../components/common/Header';
import { useAuthStore } from '../../store/authStore';
import { Colors } from '../../constants/colors';

const brandLogo = require('../../assets/logo.png');

const SettingsScreen = ({ navigation }) => {
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to log out of FitLens?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: () => logout(),
      },
    ]);
  };

  const menuItems = [
    { icon: '👤', title: 'Profile Information', sub: user?.email || '', nav: 'ProfileSettings' },
    { icon: '🔒', title: 'Change Password', sub: 'Update security password', nav: 'ChangePassword' },
    { icon: '🗑️', title: 'Delete Account', sub: 'Permanently remove user data', nav: 'DeleteAccount', danger: true },
  ];

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <Header title="Settings" />

      <ScrollView contentContainerStyle={styles.content}>
        {/* User Card */}
        <View style={styles.userCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{(user?.name || 'U').charAt(0).toUpperCase()}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.userName}>{user?.name || 'User Account'}</Text>
            <Text style={styles.userEmail}>{user?.email || 'user@example.com'}</Text>
          </View>
        </View>

        {/* Menu list */}
        <View style={styles.menuCard}>
          {menuItems.map((item, idx) => (
            <TouchableOpacity
              key={idx}
              style={[styles.menuItem, idx === menuItems.length - 1 && { borderBottomWidth: 0 }]}
              onPress={() => navigation.navigate(item.nav)}>
              <Text style={styles.menuIcon}>{item.icon}</Text>
              <View style={{ flex: 1 }}>
                <Text style={[styles.menuTitle, item.danger && { color: Colors.error }]}>
                  {item.title}
                </Text>
                <Text style={styles.menuSub}>{item.sub}</Text>
              </View>
              <Text style={styles.arrow}>›</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Logout */}
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Text style={styles.logoutText}>🚪 Log Out</Text>
        </TouchableOpacity>

        {/* Brand Logo Footer */}
        <Image source={brandLogo} style={{ width: 140, height: 100, alignSelf: 'center', marginBottom: 12 }} resizeMode="contain" />

        <Text style={styles.version}>FitLens Mobile v1.0.0 • AI Body Measurements</Text>
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16, paddingBottom: 40 },
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 20,
  },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: Colors.accent,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  avatarText: { color: Colors.primary, fontSize: 22, fontWeight: '800' },
  userName: { color: Colors.textPrimary, fontSize: 18, fontWeight: '700' },
  userEmail: { color: Colors.textSecondary, fontSize: 13, marginTop: 2 },
  menuCard: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 20,
    overflow: 'hidden',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  menuIcon: { fontSize: 22, marginRight: 16 },
  menuTitle: { color: Colors.textPrimary, fontSize: 15, fontWeight: '700' },
  menuSub: { color: Colors.textSecondary, fontSize: 12, marginTop: 2 },
  arrow: { color: Colors.textSecondary, fontSize: 20 },
  logoutBtn: {
    backgroundColor: Colors.cardBg,
    borderRadius: 14,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 24,
  },
  logoutText: { color: Colors.error, fontSize: 16, fontWeight: '700' },
  version: { color: Colors.textSecondary, fontSize: 11, textAlign: 'center' },
});

export default SettingsScreen;
