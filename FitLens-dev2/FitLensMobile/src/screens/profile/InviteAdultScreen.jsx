import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  StatusBar,
  Alert,
  ActivityIndicator,
  Share,
  Modal,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import QRCode from 'react-native-qrcode-svg';
import Header from '../../components/common/Header';
import { profileApi } from '../../api/profileApi';
import { useProfileStore } from '../../store/profileStore';
import { Colors } from '../../constants/colors';

const InviteAdultScreen = ({ navigation }) => {
  const [invites, setInvites] = useState([]);
  const [activeInvite, setActiveInvite] = useState(null);
  const [selectedRelationship, setSelectedRelationship] = useState('Friend');
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [timeLeft, setTimeLeft] = useState(null); // seconds remaining
  const [isQrModalVisible, setIsQrModalVisible] = useState(false);

  const { activeCount, pendingCount, maxSlots, fetchProfiles, activeProfile } = useProfileStore();

  const isCallerOwner = !activeProfile || Boolean(activeProfile?.is_owner || activeProfile?.profile_type === 'owner');
  const isFull = (activeCount + pendingCount) >= maxSlots;
  const pendingInvite = invites.find((i) => i.status === 'pending');

  useEffect(() => {
    loadInvites();
  }, []);

  // Countdown timer effect
  useEffect(() => {
    if (!activeInvite?.expires_at) {
      setTimeLeft(null);
      return;
    }

    const updateTimer = () => {
      const exp = new Date(activeInvite.expires_at).getTime();
      const now = Date.now();
      const diffSecs = Math.max(0, Math.floor((exp - now) / 1000));
      setTimeLeft(diffSecs);
      if (diffSecs <= 0) {
        setActiveInvite((prev) => (prev ? { ...prev, status: 'expired' } : null));
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [activeInvite?.expires_at]);

  const loadInvites = async () => {
    setIsLoading(true);
    try {
      const res = await profileApi.listInvites();
      if (res.data?.success) {
        const fetched = res.data.invites || [];
        setInvites(fetched);
      }
    } catch (e) {
      console.log('Load invites error:', e);
    }
    setIsLoading(false);
  };

  const handleCreateInvite = async () => {
    if (!isCallerOwner) {
      Alert.alert(
        'Permission Denied',
        'Only the primary account owner has permission to invite new members.'
      );
      return;
    }

    if (isFull) {
      Alert.alert(
        'Profile Limit Reached',
        `Account has reached the maximum of ${maxSlots} active profiles and reserved invitations.`
      );
      return;
    }

    setIsCreating(true);
    try {
      const res = await profileApi.createInvite({
        relationship: selectedRelationship,
        profile_type: 'adult',
      });
      // Safe debug log: log only boolean existence, never raw tokens or URLs
      console.log('[Mobile Invite] Created invite - claim_url present:', Boolean(res.data?.claim_url));
      if (res.data?.success) {
        setActiveInvite(res.data);
        await fetchProfiles();
        await loadInvites();
      } else {
        Alert.alert('Error', res.data?.error || 'Could not generate invitation');
      }
    } catch (err) {
      const msg = err.response?.data?.error || err.message || 'Failed to create invite';
      Alert.alert('Invite Error', msg);
    }
    setIsCreating(false);
  };

  const handleRevoke = async (inviteId) => {
    if (!isCallerOwner) {
      Alert.alert(
        'Permission Denied',
        'Only the primary account owner has permission to revoke invitations.'
      );
      return;
    }

    Alert.alert(
      'Revoke Invite',
      'Are you sure you want to cancel this invitation? The code will become invalid immediately.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Revoke',
          style: 'destructive',
          onPress: async () => {
            try {
              await profileApi.revokeInvite(inviteId);
              if (activeInvite?.invite_id === inviteId || activeInvite?.id === inviteId) {
                setActiveInvite(null);
              }
              await fetchProfiles();
              await loadInvites();
            } catch (err) {
              Alert.alert('Error', 'Could not revoke invitation');
            }
          },
        },
      ]
    );
  };

  const handleShare = async () => {
    if (!activeInvite?.claim_url) return;
    const shareMessage = activeInvite.invite_code
      ? `You're invited to join my FitLens account! Use invite code: ${activeInvite.invite_code} or claim your profile at: ${activeInvite.claim_url}`
      : `You're invited to join my FitLens account! Claim your profile at: ${activeInvite.claim_url}`;
    try {
      await Share.share({
        message: shareMessage,
        title: 'FitLens Profile Invitation',
      });
    } catch (e) {
      console.log('Share error:', e);
    }
  };

  const handleCopyCode = () => {
    if (!activeInvite?.invite_code) return;
    Alert.alert(
      'Invite Code',
      `Invite Code: ${activeInvite.invite_code}\n\nMembers can enter this code in the FitLens app to claim their profile.`
    );
  };

  const formatCountdown = (secs) => {
    if (secs === null || secs === undefined) return '--:--';
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <LinearGradient colors={['#0A0E27', '#1A1F3A', '#0D1B2A']} style={styles.container}>
      <StatusBar barStyle="light-content" />
      <Header title="Invite Member" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* State 1: Newly Created Invite with raw claim_url (Active QR & 15-min timer) */}
        {activeInvite && Boolean(activeInvite.claim_url) && activeInvite.status === 'pending' && (timeLeft === null || timeLeft > 0) ? (
          <View style={styles.qrCard}>
            <View style={styles.timerBadge}>
              <Text style={styles.timerIcon}>⏱️</Text>
              <Text style={styles.timerText}>
                Expires in {formatCountdown(timeLeft)}
              </Text>
            </View>

            <TouchableOpacity
              style={styles.qrWrapper}
              onPress={() => setIsQrModalVisible(true)}
              activeOpacity={0.85}
            >
              <QRCode
                value={activeInvite.claim_url}
                size={230}
                color="#000000"
                backgroundColor="#FFFFFF"
                ecl="M"
                quietZone={14}
              />
              <Text style={styles.tapEnlargeText}>🔍 Tap to enlarge for easy scanning</Text>
            </TouchableOpacity>
            <Text style={styles.qrHint}>📷 Point another phone camera at this QR code to claim</Text>

            <Text style={styles.codeLabel}>15-MINUTE INVITATION CODE</Text>
            <TouchableOpacity style={styles.codeBox} onPress={handleCopyCode} activeOpacity={0.7}>
              <Text style={styles.codeText}>{activeInvite.invite_code}</Text>
              <Text style={styles.copyHint}>Tap to view code details</Text>
            </TouchableOpacity>

            <View style={styles.btnRow}>
              <TouchableOpacity style={styles.actionBtn} onPress={handleShare}>
                <LinearGradient
                  colors={Colors.gradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.actionGradient}>
                  <Text style={styles.actionBtnText}>📤 Share Invite Link</Text>
                </LinearGradient>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.revokeBtn}
                onPress={() => handleRevoke(activeInvite.invite_id || activeInvite.id)}>
                <Text style={styles.revokeBtnText}>Revoke</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : pendingInvite && !Boolean(activeInvite?.claim_url) ? (
          /* State 2: Screen Reloaded / Navigated while invite is pending (raw token securely not stored) */
          <View style={styles.pendingNoticeCard}>
            <View style={styles.noticeBadge}>
              <Text style={styles.noticeBadgeText}>🔒 Security Protected</Text>
            </View>
            <Text style={styles.noticeTitle}>Pending Invitation Active</Text>
            <Text style={styles.noticeSub}>
              An invitation for a {pendingInvite.relationship || 'Member'} is currently active. For security, one-time QR codes and claim links are only shown immediately upon creation and are never stored in plaintext on the server.
            </Text>
            <View style={styles.noticeMetaRow}>
              <Text style={styles.noticeMetaLabel}>Status:</Text>
              <Text style={styles.noticeMetaValue}>Pending Member Claim</Text>
            </View>
            {pendingInvite.expires_at ? (
              <View style={styles.noticeMetaRow}>
                <Text style={styles.noticeMetaLabel}>Expires:</Text>
                <Text style={styles.noticeMetaValue}>
                  {new Date(pendingInvite.expires_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </Text>
              </View>
            ) : null}

            <TouchableOpacity
              style={styles.regenBtn}
              onPress={() => handleRevoke(pendingInvite.invite_id)}>
              <LinearGradient
                colors={['#E53E3E', '#C53030']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.regenGradient}>
                <Text style={styles.regenBtnText}>Revoke & Regenerate Invite</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        ) : (
          /* State 3: Generate New Invite Section */
          <View style={styles.createCard}>
            <Text style={styles.createTitle}>Generate Member Invitation</Text>
            <Text style={styles.createSub}>
              Create a secure, temporary 15-minute code or QR code to let a family member or friend join your FitLens account.
            </Text>

            <Text style={styles.sectionLabel}>Member Relationship</Text>
            <View style={styles.pillsRow}>
              {['Spouse', 'Friend', 'Parent', 'Sibling', 'Other'].map((rel) => {
                const isSelected = selectedRelationship === rel;
                return (
                  <TouchableOpacity
                    key={rel}
                    style={[styles.pill, isSelected && styles.pillActive]}
                    onPress={() => setSelectedRelationship(rel)}>
                    <Text style={[styles.pillText, isSelected && styles.pillTextActive]}>
                      {rel}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>

            <TouchableOpacity
              style={[styles.genBtn, isFull && styles.btnDisabled]}
              disabled={isFull || isCreating}
              onPress={handleCreateInvite}>
              <LinearGradient
                colors={Colors.gradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.genGradient}>
                {isCreating ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.genText}>Generate 15-Min Invite Code</Text>
                )}
              </LinearGradient>
            </TouchableOpacity>

            {isFull && (
              <Text style={styles.fullWarning}>
                ⚠️ Maximum 4 profiles reached. Revoke a pending invite or archive an existing profile to invite someone new.
              </Text>
            )}
          </View>
        )}

        {/* Existing / Pending Invites List */}
        {invites.length > 0 && (
          <View style={styles.historySection}>
            <Text style={styles.sectionHeading}>Recent Invitations</Text>
            {invites.map((inv) => (
              <View key={inv.invite_id} style={styles.inviteItem}>
                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <Text style={styles.itemRel}>{inv.relationship}</Text>
                    <View
                      style={[
                        styles.statusBadge,
                        inv.status === 'claimed'
                          ? styles.statusClaimed
                          : inv.status === 'expired'
                          ? styles.statusExpired
                          : styles.statusPending,
                      ]}>
                      <Text style={styles.statusText}>{inv.status.toUpperCase()}</Text>
                    </View>
                  </View>
                  <Text style={styles.itemMeta}>Created: {inv.created_at?.slice(0, 16)}</Text>
                </View>

                {inv.status === 'pending' && (
                  <TouchableOpacity
                    style={styles.itemRevoke}
                    onPress={() => handleRevoke(inv.invite_id)}>
                    <Text style={styles.itemRevokeText}>Cancel</Text>
                  </TouchableOpacity>
                )}
              </View>
            ))}
          </View>
        )}
      </ScrollView>

      {/* Full-Screen Enlarged QR Modal */}
      <Modal
        visible={isQrModalVisible}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setIsQrModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Scan FitLens Invitation</Text>
              <TouchableOpacity onPress={() => setIsQrModalVisible(false)} style={styles.modalCloseBtn}>
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalQrWrapper}>
              <QRCode
                value={activeInvite?.claim_url || ''}
                size={260}
                color="#000000"
                backgroundColor="#FFFFFF"
                ecl="M"
                quietZone={16}
              />
            </View>

            <Text style={styles.modalTip}>
              💡 Turn up screen brightness to make scanning easier from another phone camera.
            </Text>

            <View style={styles.modalCodeBox}>
              <Text style={styles.modalCodeLabel}>OR ENTER CODE MANUALLY</Text>
              <Text style={styles.modalCodeValue}>{activeInvite?.invite_code}</Text>
            </View>

            <TouchableOpacity
              style={styles.modalDismissBtn}
              onPress={() => setIsQrModalVisible(false)}
            >
              <Text style={styles.modalDismissText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { padding: 20, paddingBottom: 40 },
  qrCard: {
    backgroundColor: Colors.cardBg,
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 24,
  },
  timerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(237, 137, 54, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginBottom: 20,
  },
  timerIcon: { fontSize: 14, marginRight: 6 },
  timerText: { color: Colors.warning, fontWeight: '700', fontSize: 13 },
  qrWrapper: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    marginBottom: 12,
  },
  qrHint: {
    color: Colors.textSecondary,
    fontSize: 12,
    marginBottom: 16,
    textAlign: 'center',
    fontWeight: '600',
  },
  codeLabel: {
    color: Colors.textSecondary,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.5,
    marginBottom: 8,
  },
  codeBox: {
    backgroundColor: Colors.secondary,
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.accent,
    marginBottom: 20,
  },
  codeText: {
    color: Colors.accent,
    fontSize: 24,
    fontWeight: '900',
    letterSpacing: 2,
  },
  copyHint: {
    color: Colors.textSecondary,
    fontSize: 11,
    marginTop: 4,
  },
  btnRow: {
    flexDirection: 'row',
    width: '100%',
    gap: 12,
  },
  actionBtn: { flex: 1 },
  actionGradient: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  actionBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  revokeBtn: {
    paddingVertical: 14,
    paddingHorizontal: 18,
    borderRadius: 12,
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: Colors.error,
    alignItems: 'center',
    justifyContent: 'center',
  },
  revokeBtnText: {
    color: Colors.error,
    fontWeight: '700',
    fontSize: 13,
  },
  createCard: {
    backgroundColor: Colors.cardBg,
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 24,
  },
  createTitle: {
    color: Colors.textPrimary,
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 8,
  },
  createSub: {
    color: Colors.textSecondary,
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 20,
  },
  sectionLabel: {
    color: Colors.textPrimary,
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 10,
  },
  pillsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 24,
  },
  pill: {
    backgroundColor: Colors.secondary,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  pillActive: {
    backgroundColor: Colors.accent,
    borderColor: Colors.accent,
  },
  pillText: {
    color: Colors.textSecondary,
    fontSize: 13,
    fontWeight: '600',
  },
  pillTextActive: {
    color: Colors.primary,
    fontWeight: '700',
  },
  genBtn: {
    width: '100%',
  },
  btnDisabled: {
    opacity: 0.5,
  },
  genGradient: {
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
  },
  genText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 15,
  },
  fullWarning: {
    color: Colors.warning,
    fontSize: 12,
    marginTop: 12,
    textAlign: 'center',
    lineHeight: 16,
  },
  historySection: {
    marginTop: 8,
  },
  sectionHeading: {
    color: Colors.textPrimary,
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  inviteItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.cardBg,
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 8,
  },
  itemRel: {
    color: Colors.textPrimary,
    fontSize: 14,
    fontWeight: '700',
  },
  statusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  statusPending: {
    backgroundColor: 'rgba(237, 137, 54, 0.2)',
  },
  statusClaimed: {
    backgroundColor: 'rgba(72, 187, 120, 0.2)',
  },
  statusExpired: {
    backgroundColor: 'rgba(252, 129, 129, 0.2)',
  },
  statusText: {
    color: Colors.textPrimary,
    fontSize: 9,
    fontWeight: '700',
  },
  itemMeta: {
    color: Colors.textSecondary,
    fontSize: 11,
    marginTop: 4,
  },
  itemRevoke: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.error,
  },
  itemRevokeText: {
    color: Colors.error,
    fontSize: 12,
    fontWeight: '600',
  },
  pendingNoticeCard: {
    backgroundColor: Colors.cardBg,
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: 'rgba(237, 137, 54, 0.4)',
    marginBottom: 24,
  },
  noticeBadge: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(237, 137, 54, 0.15)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 12,
  },
  noticeBadgeText: {
    color: Colors.warning,
    fontSize: 12,
    fontWeight: '700',
  },
  noticeTitle: {
    color: Colors.textPrimary,
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 8,
  },
  noticeSub: {
    color: Colors.textSecondary,
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 16,
  },
  noticeMetaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  noticeMetaLabel: {
    color: Colors.textSecondary,
    fontSize: 13,
  },
  noticeMetaValue: {
    color: Colors.textPrimary,
    fontSize: 13,
    fontWeight: '600',
  },
  regenBtn: {
    marginTop: 20,
    borderRadius: 14,
    overflow: 'hidden',
  },
  regenGradient: {
    paddingVertical: 14,
    alignItems: 'center',
    borderRadius: 14,
  },
  regenBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  tapEnlargeText: {
    color: Colors.accent,
    fontSize: 11,
    fontWeight: '700',
    marginTop: 8,
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(10, 14, 39, 0.92)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalCard: {
    backgroundColor: '#1E2340',
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#2D3561',
    padding: 24,
    alignItems: 'center',
    width: '100%',
    maxWidth: 340,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    marginBottom: 16,
  },
  modalTitle: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '800',
  },
  modalCloseBtn: {
    padding: 6,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  modalCloseText: {
    color: '#A0AEC0',
    fontSize: 14,
    fontWeight: '700',
  },
  modalQrWrapper: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    marginBottom: 14,
  },
  modalTip: {
    color: '#A0AEC0',
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 16,
    marginBottom: 16,
  },
  modalCodeBox: {
    backgroundColor: '#0A0E27',
    borderWidth: 1,
    borderColor: '#00D4AA',
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 20,
    alignItems: 'center',
    width: '100%',
    marginBottom: 16,
  },
  modalCodeLabel: {
    color: '#00D4AA',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 4,
  },
  modalCodeValue: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '900',
    letterSpacing: 2,
  },
  modalDismissBtn: {
    backgroundColor: '#00D4AA',
    paddingVertical: 12,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
  },
  modalDismissText: {
    color: '#0A0E27',
    fontWeight: '800',
    fontSize: 14,
  },
});

export default InviteAdultScreen;
