import React, { useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  StatusBar,
  ActivityIndicator,
  Alert,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { useProfileStore } from '../../store/profileStore';
import { useAuthStore } from '../../store/authStore';
import { Colors } from '../../constants/colors';

// Vibrant avatar background colors for Netflix-style profile differentiation
const AVATAR_COLORS = [
  ['#00D4AA', '#0080FF'],
  ['#FF5E62', '#FF9966'],
  ['#7F00FF', '#E100FF'],
  ['#11998E', '#38EF7D'],
  ['#F7971E', '#FFD200'],
  ['#4E54C8', '#8F94FB'],
];

const ProfileSelectionScreen = ({ navigation }) => {
  const {
    profiles,
    activeProfile,
    isLoading,
    totalSlots,
    activeCount,
    pendingCount,
    maxSlots,
    fetchProfiles,
    setActiveProfile,
  } = useProfileStore();

  const { user } = useAuthStore();

  useEffect(() => {
    fetchProfiles();
  }, []);

  const isCallerOwner = !activeProfile || Boolean(activeProfile?.is_owner || activeProfile?.profile_type === 'owner');

  const handleSelectProfile = async (profile) => {
    if (profile.id !== activeProfile?.id) {
      Alert.alert(
        'Switching Disabled',
        'Profile switching between accounts is disabled. Account owners can manage family profiles via Settings > Manage Profiles.'
      );
      return;
    }
    navigation.navigate('Tabs');
  };

  const isFull = (activeCount + pendingCount) >= maxSlots;

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Top Bar */}
      <View style={styles.topBar}>
        <Text style={styles.appTitle}>FitLens</Text>
        <TouchableOpacity
          style={styles.manageBtn}
          onPress={() => navigation.navigate('ManageProfiles')}>
          <Text style={styles.manageText}>⚙️ Manage</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.titleSection}>
          <Text style={styles.heading}>Who's measuring today?</Text>
          <Text style={styles.subheading}>
            Select a profile to track personalized AI body measurements
          </Text>
        </View>

        {/* Member Mode Notice */}
        {!isCallerOwner && (
          <View style={{
            backgroundColor: 'rgba(255, 179, 0, 0.1)',
            borderColor: 'rgba(255, 179, 0, 0.35)',
            borderWidth: 1,
            borderRadius: 12,
            padding: 12,
            marginBottom: 16,
            flexDirection: 'row',
            alignItems: 'center',
            gap: 8,
          }}>
            <Text style={{ fontSize: 16 }}>🔒</Text>
            <Text style={{ color: '#FFE082', fontSize: 12, flex: 1, lineHeight: 16 }}>
              Member View ({activeProfile?.name}): You have access only to your own profile. Only the owner can invite members or add profiles.
            </Text>
          </View>
        )}

        {/* Capacity Indicator */}
        <View style={[styles.capacityCard, isFull && styles.capacityFull]}>
          <View style={styles.capacityRow}>
            <Text style={styles.capacityLabel}>Account Profile Slots</Text>
            <Text style={[styles.capacityCount, isFull && { color: Colors.warning }]}>
              {activeCount + pendingCount} / {maxSlots}
            </Text>
          </View>
          <Text style={styles.capacitySub}>
            {activeCount} active {activeCount === 1 ? 'profile' : 'profiles'}
            {pendingCount > 0 ? ` • ${pendingCount} pending invite` : ''}
          </Text>

          {isFull && (
            <View style={styles.warningBox}>
              <Text style={styles.warningText}>
                ⚠️ Profile limit reached (4/4). Archive or delete an existing profile, or revoke a pending invite, to add another.
              </Text>
            </View>
          )}
        </View>

        {isLoading && profiles.length === 0 ? (
          <View style={styles.loaderWrap}>
            <ActivityIndicator size="large" color={Colors.accent} />
            <Text style={styles.loadingText}>Loading profiles...</Text>
          </View>
        ) : (
          <View style={styles.profileGrid}>
            {profiles.map((profile, idx) => {
              const isActive = activeProfile?.id === profile.id;
              const gradColors = AVATAR_COLORS[idx % AVATAR_COLORS.length];
              const initial = (profile.name || 'P').charAt(0).toUpperCase();
              const canSelect = isActive || isCallerOwner;

              return (
                <TouchableOpacity
                  key={profile.id}
                  style={[
                    styles.profileCard,
                    isActive && styles.profileCardActive,
                    !canSelect && { opacity: 0.5 }
                  ]}
                  onPress={() => handleSelectProfile(profile)}
                  activeOpacity={canSelect ? 0.8 : 1}>
                  <LinearGradient
                    colors={gradColors}
                    style={styles.avatarCircle}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}>
                    <Text style={styles.avatarText}>{initial}</Text>
                    {isActive && (
                      <View style={styles.activeBadge}>
                        <Text style={styles.checkIcon}>✓</Text>
                      </View>
                    )}
                  </LinearGradient>

                  <Text style={styles.profileName} numberOfLines={1}>
                    {profile.name}
                  </Text>

                  <View style={styles.tagRow}>
                    {profile.is_owner ? (
                      <View style={[styles.badge, styles.ownerBadge]}>
                        <Text style={styles.badgeText}>Owner</Text>
                      </View>
                    ) : (
                      <View style={[styles.badge, styles.relBadge]}>
                        <Text style={styles.badgeText}>{profile.relationship || 'Member'}</Text>
                      </View>
                    )}

                    {profile.profile_type === 'child' && (
                      <View style={[styles.badge, styles.childBadge]}>
                        <Text style={styles.badgeText}>Child</Text>
                      </View>
                    )}

                    {!canSelect && (
                      <View style={[styles.badge, { backgroundColor: '#1E294A' }]}>
                        <Text style={[styles.badgeText, { color: Colors.textSecondary }]}>
                          {profile.is_owner ? '👑 Owner' : '🔒 Member'}
                        </Text>
                      </View>
                    )}
                  </View>

                  {profile.default_height_cm && (
                    <Text style={styles.heightText}>{profile.default_height_cm} cm</Text>
                  )}
                </TouchableOpacity>
              );
            })}

            {/* Add Profile Card - OWNER ONLY */}
            {isCallerOwner && !isFull && (
              <TouchableOpacity
                style={styles.addCard}
                onPress={() => navigation.navigate('AddProfile')}
                activeOpacity={0.7}>
                <View style={styles.addCircle}>
                  <Text style={styles.addPlus}>+</Text>
                </View>
                <Text style={styles.addText}>Add Profile</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* Action Buttons - OWNER ONLY */}
        {isCallerOwner && (
          <View style={styles.actionSection}>
            <TouchableOpacity
              style={[styles.inviteBtn, isFull && styles.btnDisabled]}
              disabled={isFull}
              onPress={() => navigation.navigate('InviteAdult')}>
              <Text style={styles.inviteBtnIcon}>✉️</Text>
              <View style={{ flex: 1, marginLeft: 12 }}>
                <Text style={styles.inviteBtnTitle}>Invite Adult Member</Text>
                <Text style={styles.inviteBtnSub}>Generate a 15-min QR code or claim code</Text>
              </View>
              <Text style={styles.arrowIcon}>›</Text>
            </TouchableOpacity>
          </View>
        )}

        {activeProfile && (
          <TouchableOpacity
            style={styles.continueBtn}
            onPress={() => navigation.navigate('Tabs')}>
            <LinearGradient
              colors={Colors.gradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.continueGradient}>
              <Text style={styles.continueText}>
                Continue as {activeProfile.name} →
              </Text>
            </LinearGradient>
          </TouchableOpacity>
        )}
      </ScrollView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 48,
    paddingBottom: 12,
  },
  appTitle: {
    color: Colors.accent,
    fontSize: 22,
    fontWeight: '900',
    letterSpacing: 1,
  },
  manageBtn: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: Colors.cardBg,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  manageText: {
    color: Colors.textSecondary,
    fontSize: 13,
    fontWeight: '600',
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  titleSection: {
    marginBottom: 20,
    alignItems: 'center',
  },
  heading: {
    color: Colors.textPrimary,
    fontSize: 24,
    fontWeight: '800',
    textAlign: 'center',
  },
  subheading: {
    color: Colors.textSecondary,
    fontSize: 13,
    textAlign: 'center',
    marginTop: 6,
  },
  capacityCard: {
    backgroundColor: Colors.cardBg,
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 24,
  },
  capacityFull: {
    borderColor: Colors.warning,
  },
  capacityRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  capacityLabel: {
    color: Colors.textPrimary,
    fontSize: 13,
    fontWeight: '700',
  },
  capacityCount: {
    color: Colors.accent,
    fontSize: 14,
    fontWeight: '800',
  },
  capacitySub: {
    color: Colors.textSecondary,
    fontSize: 12,
    marginTop: 4,
  },
  warningBox: {
    marginTop: 10,
    padding: 10,
    borderRadius: 8,
    backgroundColor: 'rgba(237, 137, 54, 0.15)',
  },
  warningText: {
    color: Colors.warning,
    fontSize: 12,
    lineHeight: 16,
  },
  loaderWrap: {
    padding: 40,
    alignItems: 'center',
  },
  loadingText: {
    color: Colors.textSecondary,
    marginTop: 12,
    fontSize: 13,
  },
  profileGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  profileCard: {
    width: '47%',
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  profileCardActive: {
    borderColor: Colors.accent,
    backgroundColor: '#1E294A',
  },
  avatarCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    position: 'relative',
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 28,
    fontWeight: '800',
  },
  activeBadge: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    backgroundColor: Colors.accent,
    width: 22,
    height: 22,
    borderRadius: 11,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: Colors.primary,
  },
  checkIcon: {
    color: Colors.primary,
    fontSize: 12,
    fontWeight: '900',
  },
  profileName: {
    color: Colors.textPrimary,
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 6,
    textAlign: 'center',
  },
  tagRow: {
    flexDirection: 'row',
    gap: 4,
    marginBottom: 6,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  ownerBadge: {
    backgroundColor: 'rgba(0, 212, 170, 0.2)',
  },
  relBadge: {
    backgroundColor: 'rgba(0, 128, 255, 0.2)',
  },
  childBadge: {
    backgroundColor: 'rgba(255, 153, 102, 0.2)',
  },
  badgeText: {
    color: Colors.textPrimary,
    fontSize: 10,
    fontWeight: '600',
  },
  heightText: {
    color: Colors.textSecondary,
    fontSize: 12,
  },
  addCard: {
    width: '47%',
    backgroundColor: 'transparent',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: Colors.border,
    marginBottom: 16,
    minHeight: 150,
  },
  addCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: Colors.cardBg,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  addPlus: {
    color: Colors.accent,
    fontSize: 32,
    fontWeight: '300',
  },
  addText: {
    color: Colors.textSecondary,
    fontSize: 14,
    fontWeight: '600',
  },
  actionSection: {
    marginBottom: 20,
  },
  inviteBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.cardBg,
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  btnDisabled: {
    opacity: 0.5,
  },
  inviteBtnIcon: {
    fontSize: 24,
  },
  inviteBtnTitle: {
    color: Colors.textPrimary,
    fontSize: 15,
    fontWeight: '700',
  },
  inviteBtnSub: {
    color: Colors.textSecondary,
    fontSize: 12,
    marginTop: 2,
  },
  arrowIcon: {
    color: Colors.textSecondary,
    fontSize: 22,
  },
  continueBtn: {
    marginTop: 10,
  },
  continueGradient: {
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
  },
  continueText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
});

export default ProfileSelectionScreen;
