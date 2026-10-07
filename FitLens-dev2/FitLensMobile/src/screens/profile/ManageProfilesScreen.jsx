import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  StatusBar,
  Alert,
  Modal,
  ActivityIndicator,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Header from '../../components/common/Header';
import { useProfileStore } from '../../store/profileStore';
import { profileApi } from '../../api/profileApi';
import { Colors } from '../../constants/colors';

const ManageProfilesScreen = ({ navigation }) => {
  const {
    profiles,
    activeProfile,
    activeCount,
    pendingCount,
    maxSlots,
    fetchProfiles,
    archiveProfile,
    deleteProfile,
  } = useProfileStore();

  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingProfile, setEditingProfile] = useState(null);
  const [editName, setEditName] = useState('');
  const [editHeight, setEditHeight] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  const isCallerOwner = Boolean(activeProfile?.is_owner || activeProfile?.profile_type === 'owner');

  const openEditModal = (profile) => {
    if (!isCallerOwner && profile.id !== activeProfile?.id) {
      Alert.alert('Permission Denied', 'You only have permission to edit your own profile.');
      return;
    }
    setEditingProfile(profile);
    setEditName(profile.name || '');
    setEditHeight(profile.default_height_cm ? String(profile.default_height_cm) : '170');
    setEditModalVisible(true);
  };

  const handleSaveEdit = async () => {
    if (!editingProfile) return;
    if (!isCallerOwner && editingProfile.id !== activeProfile?.id) {
      Alert.alert('Permission Denied', 'You only have permission to edit your own profile.');
      return;
    }
    const trimmed = editName.trim();
    if (!trimmed || trimmed.length < 1 || trimmed.length > 50) {
      Alert.alert('Invalid Name', 'Name must be between 1 and 50 characters.');
      return;
    }

    const parsedH = parseFloat(editHeight);
    if (isNaN(parsedH) || parsedH < 100 || parsedH > 250) {
      Alert.alert('Invalid Height', 'Height must be between 100 and 250 cm.');
      return;
    }

    setIsUpdating(true);
    try {
      const res = await profileApi.updateProfile(editingProfile.id, {
        name: trimmed,
        default_height_cm: parsedH,
      });

      if (res.data?.success) {
        setEditModalVisible(false);
        await fetchProfiles();
      } else {
        Alert.alert('Error', res.data?.error || 'Could not update profile');
      }
    } catch (e) {
      Alert.alert('Error', e.response?.data?.error || e.message || 'Failed to update');
    }
    setIsUpdating(false);
  };

  const handleArchive = (profile) => {
    if (!isCallerOwner) {
      Alert.alert('Permission Denied', 'Only the primary account owner has permission to archive profiles.');
      return;
    }
    if (profile.is_owner) {
      Alert.alert('Action Not Allowed', 'The primary account owner profile cannot be archived.');
      return;
    }

    Alert.alert(
      'Archive Profile',
      `Archive "${profile.name}"? This profile will be hidden from the active selection screen, freeing up 1 slot for new members. Its measurement history will be safely preserved.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Archive',
          style: 'default',
          onPress: async () => {
            const res = await archiveProfile(profile.id);
            if (!res.success) {
              Alert.alert('Error', res.error || 'Could not archive profile');
            }
          },
        },
      ]
    );
  };

  const handleDelete = (profile) => {
    if (!isCallerOwner) {
      Alert.alert('Permission Denied', 'Only the primary account owner has permission to delete profiles.');
      return;
    }
    if (profile.is_owner) {
      Alert.alert('Action Not Allowed', 'The primary account owner profile cannot be deleted.');
      return;
    }

    Alert.alert(
      'Delete Profile Permanently?',
      `Are you sure you want to permanently delete "${profile.name}"?\n\n⚠️ WARNING: All body measurements, 3D meshes, front/side photos, and overlays for this profile will be permanently erased. This action cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete Permanently',
          style: 'destructive',
          onPress: async () => {
            const res = await deleteProfile(profile.id);
            if (!res.success) {
              Alert.alert('Error', res.error || 'Could not delete profile');
            }
          },
        },
      ]
    );
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <StatusBar barStyle="light-content" />
      <Header title="Manage Profiles" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Capacity Overview */}
        <View style={styles.capacityCard}>
          <Text style={styles.capacityTitle}>Capacity Overview</Text>
          <View style={styles.capacityBar}>
            {[1, 2, 3, 4].map((slot) => {
              const isFilled = slot <= (activeCount + pendingCount);
              const isPending = slot > activeCount && slot <= (activeCount + pendingCount);
              return (
                <View
                  key={slot}
                  style={[
                    styles.slotSegment,
                    isFilled && (isPending ? styles.slotPending : styles.slotFilled),
                  ]}
                />
              );
            })}
          </View>
          <Text style={styles.capacityText}>
            {activeCount + pendingCount} of {maxSlots} slots used ({activeCount} active, {pendingCount} pending invite)
          </Text>
        </View>

        {/* Member Restriction Notice */}
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
              Member View: You only have access to edit your own profile ({activeProfile?.name}). Only the primary account owner can manage, archive, or delete profiles.
            </Text>
          </View>
        )}

        {/* Profiles List */}
        <Text style={styles.sectionHeader}>Active Profiles</Text>
        {profiles.map((p) => {
          const isOwner = p.is_owner;
          const isCurrent = activeProfile?.id === p.id;

          return (
            <View key={p.id} style={[styles.profileItem, isCurrent && styles.profileItemActive]}>
              <View style={styles.avatar}>
                <Text style={styles.avatarLetter}>{(p.name || 'P').charAt(0).toUpperCase()}</Text>
              </View>

              <View style={{ flex: 1, marginLeft: 14 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                  <Text style={styles.profileName}>{p.name}</Text>
                  {isCurrent && (
                    <View style={styles.currentBadge}>
                      <Text style={styles.currentText}>Current</Text>
                    </View>
                  )}
                </View>

                <View style={styles.metaRow}>
                  {isOwner ? (
                    <View style={[styles.badge, styles.ownerBadge]}>
                      <Text style={styles.badgeText}>Account Owner</Text>
                    </View>
                  ) : (
                    <View style={[styles.badge, styles.relBadge]}>
                      <Text style={styles.badgeText}>{p.relationship || 'Member'}</Text>
                    </View>
                  )}

                  {p.profile_type === 'child' && (
                    <View style={[styles.badge, styles.childBadge]}>
                      <Text style={styles.badgeText}>Child</Text>
                    </View>
                  )}

                  <Text style={styles.heightMeta}>{p.default_height_cm || 170} cm</Text>
                </View>
              </View>

              {/* Action buttons */}
              <View style={styles.actionColumn}>
                {(isCallerOwner || isCurrent) ? (
                  <TouchableOpacity
                    style={styles.editBtn}
                    onPress={() => openEditModal(p)}>
                    <Text style={styles.editBtnText}>✏️</Text>
                  </TouchableOpacity>
                ) : (
                  <Text style={{ fontSize: 14 }}>🔒</Text>
                )}

                {isCallerOwner && !isOwner && (
                  <View style={{ flexDirection: 'row', gap: 6, marginTop: 6 }}>
                    <TouchableOpacity
                      style={styles.archiveBtn}
                      onPress={() => handleArchive(p)}>
                      <Text style={styles.archiveBtnText}>Archive</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={styles.deleteBtn}
                      onPress={() => handleDelete(p)}>
                      <Text style={styles.deleteBtnText}>🗑️</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            </View>
          );
        })}
      </ScrollView>

      {/* Edit Profile Modal */}
      <Modal
        visible={editModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setEditModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Edit Profile</Text>

            <View style={styles.modalInputGroup}>
              <Text style={styles.modalLabel}>Name</Text>
              <TextInput
                style={styles.modalInput}
                value={editName}
                onChangeText={setEditName}
                maxLength={50}
              />
            </View>

            <View style={styles.modalInputGroup}>
              <Text style={styles.modalLabel}>Default Height (cm)</Text>
              <TextInput
                style={styles.modalInput}
                value={editHeight}
                onChangeText={setEditHeight}
                keyboardType="numeric"
                maxLength={5}
              />
            </View>

            <View style={styles.modalBtnRow}>
              <TouchableOpacity
                style={styles.cancelBtn}
                onPress={() => setEditModalVisible(false)}>
                <Text style={styles.cancelBtnText}>Cancel</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.saveBtn}
                onPress={handleSaveEdit}
                disabled={isUpdating}>
                <LinearGradient
                  colors={Colors.gradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.saveGradient}>
                  {isUpdating ? (
                    <ActivityIndicator color="#FFFFFF" size="small" />
                  ) : (
                    <Text style={styles.saveBtnText}>Save</Text>
                  )}
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { padding: 20, paddingBottom: 40 },
  capacityCard: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 24,
  },
  capacityTitle: {
    color: Colors.textPrimary,
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 10,
  },
  capacityBar: {
    flexDirection: 'row',
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.secondary,
    gap: 4,
    marginBottom: 10,
  },
  slotSegment: {
    flex: 1,
    borderRadius: 4,
    backgroundColor: Colors.secondary,
  },
  slotFilled: {
    backgroundColor: Colors.accent,
  },
  slotPending: {
    backgroundColor: Colors.warning,
  },
  capacityText: {
    color: Colors.textSecondary,
    fontSize: 12,
  },
  sectionHeader: {
    color: Colors.textPrimary,
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  profileItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.cardBg,
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 12,
  },
  profileItemActive: {
    borderColor: Colors.accent,
    backgroundColor: '#1E294A',
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.secondary,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.accent,
  },
  avatarLetter: {
    color: Colors.accent,
    fontSize: 18,
    fontWeight: '800',
  },
  profileName: {
    color: Colors.textPrimary,
    fontSize: 15,
    fontWeight: '700',
  },
  currentBadge: {
    backgroundColor: 'rgba(0, 212, 170, 0.2)',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 6,
  },
  currentText: {
    color: Colors.accent,
    fontSize: 10,
    fontWeight: '700',
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  badge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
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
  heightMeta: {
    color: Colors.textSecondary,
    fontSize: 11,
  },
  actionColumn: {
    alignItems: 'flex-end',
  },
  editBtn: {
    padding: 6,
  },
  editBtnText: {
    fontSize: 16,
  },
  archiveBtn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: Colors.secondary,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  archiveBtnText: {
    color: Colors.textSecondary,
    fontSize: 11,
    fontWeight: '600',
  },
  deleteBtn: {
    paddingHorizontal: 6,
    paddingVertical: 4,
  },
  deleteBtnText: {
    fontSize: 14,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalCard: {
    width: '100%',
    backgroundColor: Colors.cardBg,
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  modalTitle: {
    color: Colors.textPrimary,
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 20,
    textAlign: 'center',
  },
  modalInputGroup: {
    marginBottom: 16,
  },
  modalLabel: {
    color: Colors.textPrimary,
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 6,
  },
  modalInput: {
    backgroundColor: Colors.secondary,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: Colors.textPrimary,
    fontSize: 15,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  modalBtnRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 12,
  },
  cancelBtn: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  cancelBtnText: {
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  saveBtn: {
    flex: 1,
  },
  saveGradient: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  saveBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
});

export default ManageProfilesScreen;
