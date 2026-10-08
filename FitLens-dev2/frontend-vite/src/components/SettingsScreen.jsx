import React, { useState, useEffect } from 'react';
import { updateProfile, changePassword, deleteAccount, deleteMeasurement, authHeaders, getAccessMode } from '../services/authService';
import { profileService } from '../services/profileService';
import { QRCodeSVG } from 'qrcode.react';

export default function SettingsScreen({
  user,
  onUserUpdated,
  onLogout,
  onClose,
  initialTab = 'profile',
  activeProfile: propActiveProfile,
  onActiveProfileChanged
}) {
  // Restricted non-owner profile member sessions are blocked from owner settings
  if (getAccessMode() === 'invited_profile' || user?.role === 'profile_member_session' || user?.access_mode === 'invited_profile') {
    return null;
  }

  const [activeTab, setActiveTab] = useState(initialTab || 'profile');
  const [msg, setMsg] = useState(null);
  const [error, setError] = useState(null);

  // Multi-Profile State
  const [profiles, setProfiles] = useState([]);
  const [slotUsage, setSlotUsage] = useState({ active_count: 1, pending_count: 0, max_slots: 4 });
  const [currentActiveProfile, setCurrentActiveProfile] = useState(propActiveProfile || profileService.getActiveProfile());
  const [profilesLoading, setProfilesLoading] = useState(false);

  // Edit Profile State
  const [editingProfile, setEditingProfile] = useState(null);
  const [editName, setEditName] = useState('');
  const [editHeight, setEditHeight] = useState('170');
  const [editLoading, setEditLoading] = useState(false);

  // Add Profile State
  const [showAddSection, setShowAddSection] = useState(false);
  const [addName, setAddName] = useState('');
  const [addRelationship, setAddRelationship] = useState('Spouse');
  const [addHeight, setAddHeight] = useState('170');
  const [addLoading, setAddLoading] = useState(false);

  // Invite Adult State
  const [showInviteSection, setShowInviteSection] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRelationship, setInviteRelationship] = useState('Spouse');
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteResult, setInviteResult] = useState(null);
  const [pendingInvite, setPendingInvite] = useState(null);
  const [copiedType, setCopiedType] = useState(null);
  const [selectedInviteProfileId, setSelectedInviteProfileId] = useState('');
  const [invitesList, setInvitesList] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showEnlargedQr, setShowEnlargedQr] = useState(false);

  const handleCopy = (text, type) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedType(type);
    setTimeout(() => setCopiedType(null), 2500);
  };

  // Profile State
  const [name, setName] = useState(user?.name || '');
  const [profileLoading, setProfileLoading] = useState(false);

  // Security State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [securityLoading, setSecurityLoading] = useState(false);

  // History State
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Delete Account State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    fetchProfilesList();
  }, []);

  useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab);
    }
  }, [initialTab]);

  useEffect(() => {
    if (propActiveProfile) {
      setCurrentActiveProfile(propActiveProfile);
    }
  }, [propActiveProfile]);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    } else if (activeTab === 'profiles') {
      fetchProfilesList();
    }
  }, [activeTab]);

  const fetchProfilesList = async () => {
    setProfilesLoading(true);
    try {
      const data = await profileService.listProfiles();
      if (data.success) {
        const fetched = data.profiles || [];
        setProfiles(fetched);
        setSlotUsage({
          active_count: data.active_profiles_count ?? fetched.length,
          pending_count: data.pending_invites_count ?? 0,
          max_slots: data.max_allowed_slots ?? 4
        });
        const current = currentActiveProfile || propActiveProfile;
        if (current) {
          const fresh = fetched.find(p => p.id === current.id);
          if (fresh) setCurrentActiveProfile(fresh);
        } else if (fetched.length > 0) {
          setCurrentActiveProfile(fetched[0]);
          profileService.saveActiveProfile(fetched[0]);
          if (onActiveProfileChanged) onActiveProfileChanged(fetched[0]);
        }
      }

      // Also fetch invitations and in-app notifications if owner
      try {
        const invRes = await profileService.listInvites();
        if (invRes.success) {
          const allInvites = invRes.invites || [];
          setInvitesList(allInvites);
          const activePending = allInvites.find(i => ['sent', 'opened', 'verification_pending', 'pending'].includes(i.status));
          setPendingInvite(activePending || null);
        }
      } catch (invErr) {
        // Silently catch invite list errors
      }

      try {
        const notifRes = await profileService.getNotifications();
        if (notifRes.success && notifRes.notifications) {
          setNotifications(notifRes.notifications || []);
          setUnreadCount((notifRes.notifications || []).filter(n => !n.read).length);
        }
      } catch (notifErr) {
        // Silently catch notification errors
      }
    } catch (e) {
      console.error(e);
    } finally {
      setProfilesLoading(false);
    }
  };

  const isCallerOwner = () => {
    return Boolean(
      currentActiveProfile?.is_owner ||
      currentActiveProfile?.profile_type === 'owner' ||
      (user && currentActiveProfile && user.name === currentActiveProfile.name && !currentActiveProfile.relationship)
    );
  };

  const handleSwitchProfile = (p) => {
    clearAlerts();
    if (!isCallerOwner()) {
      setError('Only the account owner has permission to switch profiles. Member accounts cannot switch to the owner or other profiles.');
      return;
    }
    setCurrentActiveProfile(p);
    profileService.saveActiveProfile(p);
    if (onActiveProfileChanged) onActiveProfileChanged(p);
    setMsg(`Active profile switched to "${p.name}". Measurements are now recorded for ${p.name}.`);
  };

  const handleStartEdit = (p) => {
    clearAlerts();
    if (!isCallerOwner() && p.id !== currentActiveProfile?.id) {
      setError('You only have permission to edit your own profile.');
      return;
    }
    setEditingProfile(p);
    setEditName(p.name || '');
    setEditHeight(p.default_height_cm ? String(p.default_height_cm) : '170');
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    clearAlerts();
    if (!editingProfile) return;

    if (!isCallerOwner() && editingProfile.id !== currentActiveProfile?.id) {
      setError('You only have permission to edit your own profile.');
      return;
    }

    const trimmed = editName.trim();
    if (!trimmed || trimmed.length < 1 || trimmed.length > 50) {
      setError('Name must be between 1 and 50 characters.');
      return;
    }

    const h = parseFloat(editHeight);
    if (isNaN(h) || h < 100 || h > 250) {
      setError('Height must be between 100 and 250 cm.');
      return;
    }

    setEditLoading(true);
    try {
      const res = await profileService.updateProfile(editingProfile.id, {
        name: trimmed,
        default_height_cm: h
      });

      if (res.success) {
        setMsg(`Profile "${trimmed}" updated successfully.`);
        setEditingProfile(null);
        await fetchProfilesList();
      } else {
        setError(res.error || 'Failed to update profile.');
      }
    } catch (err) {
      setError(err.message || 'Error updating profile.');
    } finally {
      setEditLoading(false);
    }
  };

  const handleArchiveProfile = async (p) => {
    clearAlerts();
    if (!isCallerOwner()) {
      setError('Only the account owner has permission to archive profiles.');
      return;
    }
    if (p.is_owner) {
      setError('Account owner profile cannot be archived.');
      return;
    }

    if (!window.confirm(`Archive profile "${p.name}"? This profile will be archived and will free up 1 slot for new members. Measurement history is preserved.`)) {
      return;
    }

    try {
      const res = await profileService.archiveProfile(p.id);
      if (res.success) {
        setMsg(`Profile "${p.name}" has been archived.`);
        await fetchProfilesList();
      } else {
        setError(res.error || 'Failed to archive profile.');
      }
    } catch (err) {
      setError(err.message || 'Error archiving profile.');
    }
  };

  const handleDeleteProfile = async (p) => {
    clearAlerts();
    if (!isCallerOwner()) {
      setError('Only the account owner has permission to delete profiles.');
      return;
    }
    if (p.is_owner) {
      setError('Account owner profile cannot be deleted.');
      return;
    }

    if (!window.confirm(`Permanently delete profile "${p.name}"?\n\n⚠️ WARNING: This will permanently delete this profile and all associated measurements, 3D meshes, and photos. This action cannot be undone.`)) {
      return;
    }

    try {
      const res = await profileService.deleteProfile(p.id);
      if (res.success) {
        setMsg(`Profile "${p.name}" has been permanently deleted.`);
        if (currentActiveProfile?.id === p.id) {
          const owner = profiles.find(x => x.is_owner || x.profile_type === 'owner');
          if (owner) {
            handleSwitchProfile(owner);
          }
        }
        await fetchProfilesList();
      } else {
        setError(res.error || 'Failed to delete profile.');
      }
    } catch (err) {
      setError(err.message || 'Error deleting profile.');
    }
  };

  const handleCreateNewProfile = async (e) => {
    e.preventDefault();
    clearAlerts();
    if (!isCallerOwner()) {
      setError('Only the account owner has permission to create new profiles.');
      return;
    }

    const trimmed = addName.trim();
    if (!trimmed || trimmed.length < 1 || trimmed.length > 50) {
      setError('Name must be between 1 and 50 characters.');
      return;
    }

    const h = parseFloat(addHeight);
    if (isNaN(h) || h < 100 || h > 250) {
      setError('Height must be between 100 and 250 cm.');
      return;
    }

    setAddLoading(true);
    try {
      const res = await profileService.createProfile({
        name: trimmed,
        relationship: addRelationship,
        default_height_cm: h,
        profile_type: addRelationship.toLowerCase() === 'child' ? 'child' : 'adult'
      });

      if (res.success && res.profile) {
        setMsg(`Profile "${trimmed}" created successfully!`);
        setAddName('');
        setShowAddSection(false);
        await fetchProfilesList();
      } else {
        setError(res.error || 'Failed to create profile.');
      }
    } catch (err) {
      setError(err.message || 'Error creating profile.');
    } finally {
      setAddLoading(false);
    }
  };

  const handleSendInvitation = async (e) => {
    e.preventDefault();
    clearAlerts();
    setInviteResult(null);
    if (!isCallerOwner()) {
      setError('Only the account owner has permission to invite members.');
      return;
    }

    const email = inviteEmail.trim().toLowerCase();
    if (!email || !email.includes('@')) {
      setError('Please provide a valid email address.');
      return;
    }

    setInviteLoading(true);
    try {
      const res = await profileService.createInvite({
        target_email: email,
        relationship: inviteRelationship,
        profile_id: selectedInviteProfileId || undefined
      });

      // Debug safely: log ONLY boolean state, never raw tokens or URLs
      console.log('[Web Invite] Newly created invite - claim_url present:', Boolean(res?.claim_url));

      if (res.success) {
        setInviteResult(res);
        setPendingInvite(null);
        setSelectedInviteProfileId('');
        setMsg(`Invitation created for ${email}. Email sent and QR / invite link ready.`);
        setInviteEmail('');
        await fetchProfilesList();
      } else {
        setError(res.error || 'Failed to send invitation.');
      }
    } catch (err) {
      setError(err.message || 'Error sending invitation.');
    } finally {
      setInviteLoading(false);
    }
  };

  const formatDate = (isoStr) => {
    if (!isoStr) return '—';
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return isoStr;
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return isoStr;
    }
  };

  const renderStatusBadge = (statusDisplay, statusRaw) => {
    const s = (statusDisplay || statusRaw || 'sent').toLowerCase();
    let bg = 'rgba(59, 130, 246, 0.15)';
    let border = '#3B82F6';
    let color = '#60A5FA';
    let text = statusDisplay || 'Sent';

    if (s.includes('accepted') || s.includes('claim')) {
      bg = 'rgba(16, 185, 129, 0.15)';
      border = '#10B981';
      color = '#34D399';
      text = 'Accepted';
    } else if (s.includes('open')) {
      bg = 'rgba(245, 158, 11, 0.15)';
      border = '#F59E0B';
      color = '#FBBF24';
      text = 'Opened';
    } else if (s.includes('verif')) {
      bg = 'rgba(139, 92, 246, 0.15)';
      border = '#8B5CF6';
      color = '#A78BFA';
      text = 'Verification Pending';
    } else if (s.includes('expir')) {
      bg = 'rgba(107, 114, 128, 0.15)';
      border = '#6B7280';
      color = '#9CA3AF';
      text = 'Expired';
    } else if (s.includes('revok')) {
      bg = 'rgba(239, 68, 68, 0.15)';
      border = '#EF4444';
      color = '#F87171';
      text = 'Revoked';
    }

    return (
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '3px 10px',
        borderRadius: '8px',
        backgroundColor: bg,
        border: `1px solid ${border}`,
        color: color,
        fontSize: '11px',
        fontWeight: '700',
        textTransform: 'uppercase',
        letterSpacing: '0.5px'
      }}>
        ● {text}
      </span>
    );
  };

  const handleMarkNotificationRead = async (notifId) => {
    try {
      await profileService.markNotificationRead(notifId);
      setNotifications(prev => prev.map(n => n.id === notifId ? { ...n, read: true } : n));
      setUnreadCount(c => Math.max(0, c - 1));
    } catch (err) {
      console.warn('Could not mark notification read:', err);
    }
  };

  const handleRevokeInvite = async (inviteId) => {
    clearAlerts();
    if (!isCallerOwner()) {
      setError('Only the account owner has permission to revoke invitations.');
      return;
    }
    try {
      const res = await profileService.revokeInvite(inviteId);
      if (res.success) {
        setMsg('Invitation revoked successfully. You can now generate a new invitation.');
        setInviteResult(null);
        setPendingInvite(null);
        await fetchProfilesList();
      } else {
        setError(res.error || 'Failed to revoke invitation.');
      }
    } catch (err) {
      setError(err.message || 'Error revoking invitation.');
    }
  };

  const handleShareInvite = async () => {
    if (!inviteResult?.claim_url) return;
    if (typeof navigator !== 'undefined' && navigator.share) {
      try {
        await navigator.share({
          title: 'FitLens Profile Invitation',
          text: `You're invited to join my FitLens account! Use invite code ${inviteResult.invite_code} or claim your profile with this link:`,
          url: inviteResult.claim_url
        });
      } catch (err) {
        // User cancelled or share dismissed
      }
    } else {
      handleCopy(inviteResult.claim_url, 'claim_url');
    }
  };

  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await fetch('http://localhost:5000/api/measurements/history', {
        headers: authHeaders()
      });
      const data = await res.json();
      if (data.success) {
        setHistory(data.history || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setHistoryLoading(false);
    }
  };

  const clearAlerts = () => {
    setMsg(null);
    setError(null);
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    clearAlerts();
    if (!name.trim() || name.trim().length < 2 || name.trim().length > 50) {
      setError('Name must be between 2 and 50 characters.');
      return;
    }

    setProfileLoading(true);
    try {
      const res = await updateProfile(name.trim());
      if (res.success) {
        setMsg('Profile updated successfully.');
        const updated = { ...user, name: name.trim() };
        localStorage.setItem('fitlens_user', JSON.stringify(updated));
        if (onUserUpdated) onUserUpdated(updated);
      } else {
        setError(res.error || 'Failed to update profile.');
      }
    } catch (e) {
      setError('Error updating profile.');
    } finally {
      setProfileLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    clearAlerts();

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match.');
      return;
    }

    if (newPassword.length < 8 || !/\d/.test(newPassword)) {
      setError('New password must be at least 8 characters and contain at least 1 number.');
      return;
    }

    setSecurityLoading(true);
    try {
      const res = await changePassword(currentPassword, newPassword, confirmPassword);
      if (res.success) {
        setMsg('Password changed successfully.');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
      } else {
        setError(res.error || 'Failed to change password.');
      }
    } catch (e) {
      setError('Error changing password.');
    } finally {
      setSecurityLoading(false);
    }
  };

  const handleDeleteScan = async (analysisId) => {
    clearAlerts();
    try {
      const res = await deleteMeasurement(analysisId);
      if (res.success) {
        setHistory(prev => prev.filter(item => item.analysis_id !== analysisId));
        setMsg('Scan deleted successfully.');
      } else {
        setError(res.error || 'Failed to delete scan.');
      }
    } catch (e) {
      setError('Error deleting scan.');
    }
  };

  const handleDeleteAccount = async (e) => {
    e.preventDefault();
    clearAlerts();
    if (!deletePassword) {
      setError('Password confirmation is required to delete account.');
      return;
    }

    setDeleteLoading(true);
    try {
      const res = await deleteAccount(deletePassword);
      if (res.success) {
        alert('Account deleted successfully.');
        onLogout();
      } else {
        setError(res.error || 'Failed to delete account.');
      }
    } catch (e) {
      setError('Error deleting account.');
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div style={{
      maxWidth: '850px',
      margin: '20px auto',
      backgroundColor: '#1E2340',
      borderRadius: '24px',
      border: '1px solid #2D3561',
      boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
      overflow: 'hidden',
      color: '#ffffff',
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        padding: '24px 32px',
        borderBottom: '1px solid #2D3561',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'linear-gradient(90deg, #1A1F3C 0%, #1E2340 100%)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '24px' }}>⚙️</span>
          <h2 style={{ margin: 0, fontSize: '22px', fontWeight: '800' }}>Account Settings</h2>
          {unreadCount > 0 && (
            <span style={{
              backgroundColor: '#00D4AA',
              color: '#0a0e27',
              borderRadius: '12px',
              padding: '2px 10px',
              fontSize: '11px',
              fontWeight: '800',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              🔔 {unreadCount} new alert{unreadCount > 1 ? 's' : ''}
            </span>
          )}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            style={{
              background: '#0a0e27',
              border: '1px solid #2D3561',
              color: '#a0aec0',
              padding: '8px 16px',
              borderRadius: '10px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            ✖ Close
          </button>
        )}
      </div>

      {/* Navigation Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #2D3561',
        backgroundColor: '#0a0e27',
        overflowX: 'auto'
      }}>
        {[
          { key: 'profile', label: '👤 Profile' },
          { key: 'profiles', label: isCallerOwner() ? (unreadCount > 0 ? `👥 Manage Profiles (${unreadCount})` : '👥 Manage Profiles') : '👥 Family Profiles' },
          { key: 'security', label: '🔒 Security' },
          { key: 'history', label: '📊 Scan History' },
          { key: 'account', label: '⚠️ Account' },
          { key: 'about', label: 'ℹ️ About' }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => { setActiveTab(tab.key); clearAlerts(); }}
            style={{
              padding: '16px 24px',
              background: activeTab === tab.key ? '#1E2340' : 'transparent',
              color: activeTab === tab.key ? '#00D4AA' : '#a0aec0',
              border: 'none',
              borderBottom: activeTab === tab.key ? '3px solid #00D4AA' : '3px solid transparent',
              cursor: 'pointer',
              fontWeight: '700',
              fontSize: '14px',
              whiteSpace: 'nowrap',
              transition: 'all 0.2s'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Body Content */}
      <div style={{ padding: '32px' }}>
        {msg && (
          <div style={{
            backgroundColor: 'rgba(0, 212, 170, 0.15)',
            border: '1px solid #00D4AA',
            color: '#00D4AA',
            borderRadius: '10px',
            padding: '12px 16px',
            fontSize: '14px',
            marginBottom: '20px'
          }}>
            ✅ {msg}
          </div>
        )}

        {error && (
          <div style={{
            backgroundColor: 'rgba(252, 129, 129, 0.15)',
            border: '1px solid #fc8181',
            color: '#fc8181',
            borderRadius: '10px',
            padding: '12px 16px',
            fontSize: '14px',
            marginBottom: '20px'
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Tab 1: Profile */}
        {activeTab === 'profile' && (
          <div>
            <h3 style={{ marginTop: 0, color: '#ffffff' }}>Profile Details</h3>
            <form onSubmit={handleUpdateProfile} style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '450px' }}>
              <div>
                <label style={{ display: 'block', color: '#a0aec0', fontSize: '13px', marginBottom: '8px' }}>
                  Email Address (Read-Only)
                </label>
                <input
                  type="text"
                  value={user?.email || ''}
                  disabled
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '10px',
                    color: '#718096',
                    cursor: 'not-allowed',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', color: '#a0aec0', fontSize: '13px', marginBottom: '8px' }}>
                  Full Name (2-50 characters)
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '10px',
                    color: '#ffffff',
                    fontSize: '15px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={profileLoading}
                style={{
                  width: 'fit-content',
                  padding: '12px 28px',
                  backgroundColor: '#00D4AA',
                  border: 'none',
                  borderRadius: '10px',
                  color: '#0a0e27',
                  fontWeight: '700',
                  cursor: profileLoading ? 'wait' : 'pointer'
                }}
              >
                {profileLoading ? 'Saving...' : 'Save Profile'}
              </button>
            </form>
          </div>
        )}

        {/* Tab 2: Switch Profile & Family Management */}
        {activeTab === 'profiles' && (() => {
          const ownerProfile = profiles.find(p => p.is_owner || p.profile_type === 'owner');
          const isCurrentOwner = Boolean(
            currentActiveProfile?.is_owner ||
            currentActiveProfile?.profile_type === 'owner' ||
            (user && currentActiveProfile && user.name === currentActiveProfile.name && !currentActiveProfile.relationship)
          );

          return (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
                <div>
                  <h3 style={{ margin: 0, color: '#ffffff', fontSize: '20px', fontWeight: '800' }}>
                    {isCurrentOwner ? '👥 Manage Family Profiles' : '👥 Family Profiles'}
                  </h3>
                  <p style={{ margin: '4px 0 0', color: '#a0aec0', fontSize: '13px' }}>
                    {isCurrentOwner
                      ? 'Manage family profiles, invite members, and add up to 4 profiles per account.'
                      : 'View family profiles and edit your profile details.'}
                  </p>
                </div>

                {/* Slot Counter Badge */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  backgroundColor: '#0a0e27',
                  border: '1px solid #2D3561',
                  borderRadius: '12px',
                  padding: '8px 14px'
                }}>
                  <span style={{ fontSize: '13px', color: '#a0aec0' }}>Slots:</span>
                  <strong style={{ color: (slotUsage.active_count || profiles.length) >= (slotUsage.max_slots || 4) ? '#fc8181' : '#00D4AA', fontSize: '14px' }}>
                    {slotUsage.active_count || profiles.length} / {slotUsage.max_slots || 4} Active
                  </strong>
                  <span style={{
                    fontSize: '11px',
                    padding: '2px 8px',
                    borderRadius: '10px',
                    backgroundColor: (slotUsage.active_count || profiles.length) >= (slotUsage.max_slots || 4) ? 'rgba(252, 129, 129, 0.2)' : 'rgba(0, 212, 170, 0.2)',
                    color: (slotUsage.active_count || profiles.length) >= (slotUsage.max_slots || 4) ? '#fc8181' : '#00D4AA',
                    fontWeight: '700'
                  }}>
                    {(slotUsage.active_count || profiles.length) >= (slotUsage.max_slots || 4) ? 'Full' : `${(slotUsage.max_slots || 4) - (slotUsage.active_count || profiles.length)} available`}
                  </span>
                </div>
              </div>

              {/* Member Profile Notice Banner */}
              {!isCurrentOwner && (
                <div style={{
                  backgroundColor: 'rgba(255, 179, 0, 0.1)',
                  border: '1px solid rgba(255, 179, 0, 0.35)',
                  borderRadius: '12px',
                  padding: '14px 18px',
                  marginBottom: '20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px'
                }}>
                  <span style={{ fontSize: '22px' }}>🔒</span>
                  <div style={{ fontSize: '13px', color: '#ffe082', lineHeight: '1.5' }}>
                    <strong>Member Account View ({currentActiveProfile?.name}):</strong> You only have access to your own profile. You cannot switch between profiles. Only the account owner has access to manage family profiles and invite members.
                  </div>
                </div>
              )}

              {/* Currently Active Profile Card */}
              {currentActiveProfile && (
                <div style={{
                  backgroundColor: 'rgba(0, 212, 170, 0.08)',
                  border: '1px solid #00D4AA',
                  borderRadius: '16px',
                  padding: '16px 20px',
                  marginBottom: '24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '12px',
                  boxShadow: '0 4px 16px rgba(0, 212, 170, 0.15)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{
                      width: '46px',
                      height: '46px',
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #00D4AA, #0080FF)',
                      color: '#0a0e27',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: '800',
                      fontSize: '18px'
                    }}>
                      {(currentActiveProfile.name || 'U').charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <h4 style={{ margin: 0, color: '#ffffff', fontSize: '16px', fontWeight: '700' }}>
                          {currentActiveProfile.name}
                        </h4>
                        <span style={{
                          fontSize: '10px',
                          backgroundColor: '#00D4AA',
                          color: '#0a0e27',
                          padding: '2px 8px',
                          borderRadius: '10px',
                          fontWeight: '800',
                          textTransform: 'uppercase'
                        }}>
                          ✓ Currently Active
                        </span>
                        <span style={{
                          fontSize: '11px',
                          backgroundColor: '#2D3561',
                          color: '#a0aec0',
                          padding: '2px 8px',
                          borderRadius: '10px',
                          fontWeight: '600'
                        }}>
                          {currentActiveProfile.is_owner ? 'Account Owner' : (currentActiveProfile.relationship || 'Member')}
                        </span>
                      </div>
                      <p style={{ margin: '4px 0 0', color: '#a0aec0', fontSize: '13px' }}>
                        Default Height: <strong style={{ color: '#ffffff' }}>{currentActiveProfile.default_height_cm || 170} cm</strong> • Measurements taken are saved under this profile.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleStartEdit(currentActiveProfile)}
                    style={{
                      backgroundColor: '#1E2340',
                      border: '1px solid #2D3561',
                      color: '#00D4AA',
                      padding: '8px 14px',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontWeight: '600',
                      fontSize: '13px'
                    }}
                  >
                    ✏️ Edit Profile
                  </button>
                </div>
              )}

              {/* List of Profiles */}
              <div style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h4 style={{ margin: 0, color: '#cbd5e0', fontSize: '15px', fontWeight: '700' }}>
                    All Profiles ({profiles.length})
                  </h4>
                  <button
                    onClick={fetchProfilesList}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#0a0e27',
                      border: '1px solid #2D3561',
                      borderRadius: '8px',
                      color: '#00D4AA',
                      cursor: 'pointer',
                      fontWeight: '600',
                      fontSize: '12px'
                    }}
                  >
                    🔄 Refresh
                  </button>
                </div>

                {profilesLoading ? (
                  <p style={{ color: '#a0aec0' }}>Loading profiles...</p>
                ) : profiles.length === 0 ? (
                  <p style={{ color: '#a0aec0' }}>No profiles found.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {profiles.map(p => {
                      const isActive = currentActiveProfile?.id === p.id;
                      return (
                        <div
                          key={p.id}
                          style={{
                            backgroundColor: '#0a0e27',
                            border: `1px solid ${isActive ? '#00D4AA' : '#2D3561'}`,
                            borderRadius: '14px',
                            padding: '16px 20px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            gap: '14px',
                            transition: 'all 0.2s ease'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 }}>
                            <div style={{
                              width: '40px',
                              height: '40px',
                              borderRadius: '50%',
                              backgroundColor: isActive ? '#00D4AA' : '#2D3561',
                              color: isActive ? '#0a0e27' : '#ffffff',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontWeight: '800',
                              fontSize: '16px',
                              flexShrink: 0
                            }}>
                              {(p.name || 'U').charAt(0).toUpperCase()}
                            </div>

                            <div style={{ minWidth: 0 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                <strong style={{ color: '#ffffff', fontSize: '15px' }}>{p.name}</strong>
                                <span style={{
                                  fontSize: '11px',
                                  backgroundColor: p.is_owner ? 'rgba(0, 212, 170, 0.2)' : 'rgba(160, 174, 192, 0.15)',
                                  color: p.is_owner ? '#00D4AA' : '#a0aec0',
                                  padding: '2px 8px',
                                  borderRadius: '10px',
                                  fontWeight: '700'
                                }}>
                                  {p.is_owner ? 'Owner' : (p.relationship || 'Member')}
                                </span>
                                {isActive && (
                                  <span style={{
                                    fontSize: '11px',
                                    color: '#00D4AA',
                                    fontWeight: '700'
                                  }}>
                                    ✓ Active
                                  </span>
                                )}
                              </div>
                              <div style={{ color: '#a0aec0', fontSize: '12px', marginTop: '3px' }}>
                                Default Height: <strong style={{ color: '#ffffff' }}>{p.default_height_cm || 170} cm</strong>
                                {p.email && (
                                  <span style={{ color: '#00D4AA' }}> • ✉️ {p.email}</span>
                                )}
                                {p.latest_measurement_date && (
                                  <span> • Last scan: {p.latest_measurement_date}</span>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Profile Action Buttons */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                            {isActive ? (
                              <span style={{
                                padding: '6px 12px',
                                backgroundColor: 'rgba(0, 212, 170, 0.15)',
                                border: '1px solid #00D4AA',
                                color: '#00D4AA',
                                borderRadius: '8px',
                                fontSize: '12px',
                                fontWeight: '700'
                              }}>
                                Current
                              </span>
                            ) : (
                              <span style={{
                                padding: '6px 12px',
                                backgroundColor: '#161B36',
                                border: '1px solid #2D3561',
                                color: p.is_owner ? '#00D4AA' : '#a0aec0',
                                borderRadius: '8px',
                                fontSize: '11px',
                                fontWeight: '700'
                              }}>
                                {p.is_owner ? '👑 Owner' : '👥 Member'}
                              </span>
                            )}

                            {/* Edit button: Owner can edit all; Members can only edit their own profile */}
                            {(isCurrentOwner || isActive) && (
                              <button
                                onClick={() => handleStartEdit(p)}
                                style={{
                                  backgroundColor: '#1E2340',
                                  border: '1px solid #2D3561',
                                  color: '#cbd5e0',
                                  padding: '8px 12px',
                                  borderRadius: '8px',
                                  fontWeight: '600',
                                  fontSize: '13px',
                                  cursor: 'pointer'
                                }}
                                title={isActive ? "Edit My Profile" : "Edit Profile"}
                              >
                                ✏️ Edit
                              </button>
                            )}

                            {/* Invite, Archive & Delete buttons: ONLY owner can invite, archive or permanently delete non-owner profiles */}
                            {isCurrentOwner && !p.is_owner && (
                              <div style={{ display: 'flex', gap: '6px' }}>
                                <button
                                  onClick={() => {
                                    setSelectedInviteProfileId(p.id);
                                    setInviteRelationship(p.relationship || 'Spouse');
                                    setShowInviteSection(true);
                                    setShowAddSection(false);
                                  }}
                                  style={{
                                    backgroundColor: 'rgba(0, 212, 170, 0.12)',
                                    border: '1px solid rgba(0, 212, 170, 0.4)',
                                    color: '#00D4AA',
                                    padding: '8px 12px',
                                    borderRadius: '8px',
                                    fontWeight: '600',
                                    fontSize: '13px',
                                    cursor: 'pointer',
                                    transition: 'all 0.15s ease'
                                  }}
                                  title="Generate invitation QR & deep link for this profile"
                                >
                                  ✉️ Invite
                                </button>
                                <button
                                  onClick={() => handleArchiveProfile(p)}
                                  style={{
                                    backgroundColor: 'rgba(255, 179, 0, 0.12)',
                                    border: '1px solid rgba(255, 179, 0, 0.4)',
                                    color: '#ffe082',
                                    padding: '8px 12px',
                                    borderRadius: '8px',
                                    fontWeight: '600',
                                    fontSize: '13px',
                                    cursor: 'pointer',
                                    transition: 'all 0.15s ease'
                                  }}
                                  title="Archive Profile (frees up 1 slot, preserves past measurements)"
                                >
                                  📦 Archive
                                </button>
                                <button
                                  onClick={() => handleDeleteProfile(p)}
                                  style={{
                                    backgroundColor: 'rgba(252, 129, 129, 0.12)',
                                    border: '1px solid rgba(252, 129, 129, 0.4)',
                                    color: '#fc8181',
                                    padding: '8px 12px',
                                    borderRadius: '8px',
                                    fontWeight: '600',
                                    fontSize: '13px',
                                    cursor: 'pointer',
                                    transition: 'all 0.15s ease'
                                  }}
                                  title="Permanently Delete Profile and erase all its scan data"
                                >
                                  🗑️ Delete
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Action Buttons to Add or Invite - OWNER ONLY */}
              {isCurrentOwner && (
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '24px' }}>
                  {(slotUsage.active_count || profiles.length) < (slotUsage.max_slots || 4) ? (
                    <>
                      <button
                        onClick={() => { setShowAddSection(!showAddSection); setShowInviteSection(false); }}
                        style={{
                          padding: '10px 18px',
                          backgroundColor: showAddSection ? '#2D3561' : '#00D4AA',
                          color: showAddSection ? '#ffffff' : '#0a0e27',
                          border: 'none',
                          borderRadius: '10px',
                          fontWeight: '700',
                          fontSize: '13px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}
                      >
                        <span>{showAddSection ? '✕ Cancel' : '➕ Add Family Profile'}</span>
                      </button>

                      <button
                        onClick={() => { setShowInviteSection(!showInviteSection); setShowAddSection(false); }}
                        style={{
                          padding: '10px 18px',
                          backgroundColor: showInviteSection ? '#2D3561' : 'transparent',
                          color: showInviteSection ? '#ffffff' : '#00D4AA',
                          border: '1px solid #2D3561',
                          borderRadius: '10px',
                          fontWeight: '700',
                          fontSize: '13px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}
                      >
                        <span>{showInviteSection ? '✕ Cancel' : '✉️ Invite Adult Member'}</span>
                      </button>
                    </>
                  ) : (
                    <div style={{
                      padding: '12px 18px',
                      backgroundColor: 'rgba(252, 129, 129, 0.1)',
                      border: '1px solid #fc8181',
                      borderRadius: '10px',
                      color: '#fc8181',
                      fontSize: '13px',
                      width: '100%'
                    }}>
                      ⚠️ Maximum profile slots reached (4/4). Archive an existing profile to add or invite new members.
                    </div>
                  )}
                </div>
              )}

              {/* Inline Add Profile Form - OWNER ONLY */}
              {isCurrentOwner && showAddSection && (
              <div style={{
                backgroundColor: '#0a0e27',
                border: '1px solid #00D4AA',
                borderRadius: '16px',
                padding: '24px',
                marginBottom: '24px'
              }}>
                <h4 style={{ margin: '0 0 16px 0', color: '#00D4AA', fontSize: '16px', fontWeight: '700' }}>
                  ➕ Add New Family Profile
                </h4>
                <form onSubmit={handleCreateNewProfile} style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '480px' }}>
                  <div>
                    <label style={{ display: 'block', color: '#a0aec0', fontSize: '12px', fontWeight: '700', marginBottom: '6px' }}>
                      FULL NAME
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Sarah, Alex, or Child"
                      value={addName}
                      onChange={(e) => setAddName(e.target.value)}
                      required
                      style={{
                        width: '100%',
                        padding: '12px 14px',
                        backgroundColor: '#1E2340',
                        border: '1px solid #2D3561',
                        borderRadius: '10px',
                        color: '#ffffff',
                        fontSize: '14px',
                        outline: 'none',
                        boxSizing: 'border-box'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', color: '#a0aec0', fontSize: '12px', fontWeight: '700', marginBottom: '6px' }}>
                      RELATIONSHIP
                    </label>
                    <select
                      value={addRelationship}
                      onChange={(e) => setAddRelationship(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '12px 14px',
                        backgroundColor: '#1E2340',
                        border: '1px solid #2D3561',
                        borderRadius: '10px',
                        color: '#ffffff',
                        fontSize: '14px',
                        outline: 'none',
                        boxSizing: 'border-box'
                      }}
                    >
                      <option value="Spouse">Spouse</option>
                      <option value="Child">Child</option>
                      <option value="Parent">Parent</option>
                      <option value="Sibling">Sibling</option>
                      <option value="Friend">Friend</option>
                      <option value="Family">Family Member</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', color: '#a0aec0', fontSize: '12px', fontWeight: '700', marginBottom: '6px' }}>
                      DEFAULT HEIGHT (CM)
                    </label>
                    <input
                      type="number"
                      placeholder="170"
                      min="100"
                      max="250"
                      step="0.5"
                      value={addHeight}
                      onChange={(e) => setAddHeight(e.target.value)}
                      required
                      style={{
                        width: '100%',
                        padding: '12px 14px',
                        backgroundColor: '#1E2340',
                        border: '1px solid #2D3561',
                        borderRadius: '10px',
                        color: '#ffffff',
                        fontSize: '14px',
                        outline: 'none',
                        boxSizing: 'border-box'
                      }}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                    <button
                      type="submit"
                      disabled={addLoading}
                      style={{
                        padding: '12px 24px',
                        backgroundColor: '#00D4AA',
                        border: 'none',
                        borderRadius: '10px',
                        color: '#0a0e27',
                        fontWeight: '700',
                        cursor: addLoading ? 'wait' : 'pointer'
                      }}
                    >
                      {addLoading ? 'Creating Profile...' : 'Create & Select Profile'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowAddSection(false)}
                      style={{
                        padding: '12px 20px',
                        backgroundColor: '#1E2340',
                        border: '1px solid #2D3561',
                        borderRadius: '10px',
                        color: '#a0aec0',
                        fontWeight: '600',
                        cursor: 'pointer'
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Inline Invite Adult Form - OWNER ONLY */}
            {isCurrentOwner && showInviteSection && (
              <div style={{
                backgroundColor: '#0a0e27',
                border: '1px solid #00D4AA',
                borderRadius: '16px',
                padding: '24px',
                marginBottom: '24px'
              }}>
                <h4 style={{ margin: '0 0 16px 0', color: '#00D4AA', fontSize: '16px', fontWeight: '700' }}>
                  ✉️ Invite Adult Member
                </h4>
                <p style={{ color: '#a0aec0', fontSize: '13px', margin: '0 0 16px 0' }}>
                  An invitation will be generated. The invited person can link their account to join this family profile.
                </p>
                <form onSubmit={handleSendInvitation} style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '480px' }}>
                  <div>
                    <label style={{ display: 'block', color: '#a0aec0', fontSize: '12px', fontWeight: '700', marginBottom: '6px' }}>
                      ASSIGN TO PROFILE (OPTIONAL)
                    </label>
                    <select
                      value={selectedInviteProfileId}
                      onChange={(e) => {
                        setSelectedInviteProfileId(e.target.value);
                        const found = profiles.find(p => p.id === e.target.value);
                        if (found?.relationship) setInviteRelationship(found.relationship);
                      }}
                      style={{
                        width: '100%',
                        padding: '12px 14px',
                        backgroundColor: '#1E2340',
                        border: '1px solid #2D3561',
                        borderRadius: '10px',
                        color: '#ffffff',
                        fontSize: '14px',
                        outline: 'none',
                        boxSizing: 'border-box'
                      }}
                    >
                      <option value="">Create new profile automatically</option>
                      {profiles.filter(p => !p.is_owner).map(p => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.relationship || 'Member'})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', color: '#a0aec0', fontSize: '12px', fontWeight: '700', marginBottom: '6px' }}>
                      INVITEE EMAIL ADDRESS
                    </label>
                    <input
                      type="email"
                      placeholder="e.g. spouse@example.com"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      required
                      style={{
                        width: '100%',
                        padding: '12px 14px',
                        backgroundColor: '#1E2340',
                        border: '1px solid #2D3561',
                        borderRadius: '10px',
                        color: '#ffffff',
                        fontSize: '14px',
                        outline: 'none',
                        boxSizing: 'border-box'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', color: '#a0aec0', fontSize: '12px', fontWeight: '700', marginBottom: '6px' }}>
                      RELATIONSHIP
                    </label>
                    <select
                      value={inviteRelationship}
                      onChange={(e) => setInviteRelationship(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '12px 14px',
                        backgroundColor: '#1E2340',
                        border: '1px solid #2D3561',
                        borderRadius: '10px',
                        color: '#ffffff',
                        fontSize: '14px',
                        outline: 'none',
                        boxSizing: 'border-box'
                      }}
                    >
                      <option value="Spouse">Spouse</option>
                      <option value="Partner">Partner</option>
                      <option value="Parent">Parent</option>
                      <option value="Sibling">Sibling</option>
                      <option value="Friend">Friend</option>
                      <option value="Family">Family Member</option>
                    </select>
                  </div>

                  <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                    <button
                      type="submit"
                      disabled={inviteLoading}
                      style={{
                        padding: '12px 24px',
                        backgroundColor: '#00D4AA',
                        border: 'none',
                        borderRadius: '10px',
                        color: '#0a0e27',
                        fontWeight: '700',
                        cursor: inviteLoading ? 'wait' : 'pointer'
                      }}
                    >
                      {inviteLoading ? 'Sending...' : 'Send Invitation'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowInviteSection(false)}
                      style={{
                        padding: '12px 20px',
                        backgroundColor: '#1E2340',
                        border: '1px solid #2D3561',
                        borderRadius: '10px',
                        color: '#a0aec0',
                        fontWeight: '600',
                        cursor: 'pointer'
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </form>

                {/* 1. Newly created invite with raw claim_url: Display QR code, code box, links, and share action */}
                {inviteResult && Boolean(inviteResult.claim_url) && (
                  <div style={{
                    marginTop: '20px',
                    padding: '24px',
                    backgroundColor: '#131838',
                    border: '1px solid #00D4AA',
                    borderRadius: '16px',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
                      <strong style={{ color: '#00D4AA', fontSize: '16px' }}>
                        🎉 Invitation Created Successfully!
                      </strong>
                      <span style={{ fontSize: '12px', color: '#fed7aa', backgroundColor: 'rgba(237, 137, 54, 0.2)', padding: '4px 10px', borderRadius: '12px', fontWeight: '700' }}>
                        ⏱️ Expires in 15 mins
                      </span>
                    </div>

                    {inviteResult.target_email && (
                      <div style={{ marginBottom: '16px' }}>
                        <p style={{ margin: '0 0 8px', color: '#cbd5e0', fontSize: '13px' }}>
                          {inviteResult.email_sent ? '✉️ Invitation email sent to ' : 'Recipient: '}
                          <strong style={{ color: '#ffffff' }}>{inviteResult.target_email}</strong>.
                        </p>
                        <div style={{
                          padding: '10px 14px',
                          backgroundColor: 'rgba(255, 179, 0, 0.12)',
                          border: '1px solid rgba(255, 179, 0, 0.35)',
                          borderRadius: '8px',
                          fontSize: '12px',
                          color: '#ffe082',
                          lineHeight: '1.5'
                        }}>
                          📂 <strong>Check Spam / Junk Folder:</strong> Because this email is sent from a local development environment, Gmail often places it in the recipient's <strong>Spam</strong> or <strong>Promotions</strong> folder. Ask them to check <strong>Spam</strong> and click <em>"Report not spam"</em>, or scan the QR code / share the code below.
                        </div>
                      </div>
                    )}

                    {/* QR Code Container (Optimized for Mobile Camera Scanning) */}
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      backgroundColor: '#0a0e27',
                      border: '1px solid #2D3561',
                      borderRadius: '16px',
                      padding: '24px 20px',
                      marginBottom: '18px',
                      textAlign: 'center'
                    }}>
                      <div
                        onClick={() => setShowEnlargedQr(true)}
                        title="Click to enlarge QR code for easy phone scanning"
                        style={{
                          padding: '20px',
                          backgroundColor: '#FFFFFF',
                          borderRadius: '20px',
                          boxShadow: '0 12px 36px rgba(0, 212, 170, 0.35)',
                          display: 'inline-block',
                          cursor: 'pointer',
                          transition: 'transform 0.2s ease',
                          maxWidth: '100%',
                          boxSizing: 'border-box'
                        }}
                      >
                        <QRCodeSVG
                          value={inviteResult.claim_url}
                          size={240}
                          level="M"
                          includeMargin={true}
                          fgColor="#000000"
                          bgColor="#FFFFFF"
                        />
                      </div>

                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '14px', flexWrap: 'wrap', justifyContent: 'center' }}>
                        <button
                          type="button"
                          onClick={() => setShowEnlargedQr(true)}
                          style={{
                            padding: '6px 14px',
                            backgroundColor: 'rgba(0, 212, 170, 0.15)',
                            border: '1px solid #00D4AA',
                            borderRadius: '20px',
                            color: '#00D4AA',
                            fontSize: '12px',
                            fontWeight: '700',
                            cursor: 'pointer'
                          }}
                        >
                          🔍 Tap to Enlarge QR Code
                        </button>
                        <button
                          type="button"
                          onClick={handleShareInvite}
                          style={{
                            padding: '6px 14px',
                            backgroundColor: '#1E2340',
                            border: '1px solid #2D3561',
                            borderRadius: '20px',
                            color: '#cbd5e0',
                            fontSize: '12px',
                            fontWeight: '600',
                            cursor: 'pointer'
                          }}
                        >
                          📤 Share Link
                        </button>
                      </div>

                      <p style={{ color: '#ffffff', fontSize: '13px', fontWeight: '700', marginTop: '12px', marginBottom: '2px' }}>
                        📷 Scan QR code with phone camera to claim profile instantly
                      </p>
                      <span style={{ color: '#a0aec0', fontSize: '11px', lineHeight: '1.4' }}>
                        Ensure the phone is connected to the same Wi-Fi network ({inviteResult.local_ip || 'Local Network'})
                      </span>
                    </div>

                    {/* Enlarged Fullscreen QR Modal */}
                    {showEnlargedQr && (
                      <div
                        onClick={() => setShowEnlargedQr(false)}
                        style={{
                          position: 'fixed',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundColor: 'rgba(5, 7, 20, 0.95)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          zIndex: 9999,
                          backdropFilter: 'blur(10px)',
                          padding: '20px'
                        }}
                      >
                        <div
                          onClick={(e) => e.stopPropagation()}
                          style={{
                            backgroundColor: '#131838',
                            border: '2px solid #00D4AA',
                            borderRadius: '24px',
                            padding: '30px 24px',
                            maxWidth: '380px',
                            width: '100%',
                            textAlign: 'center',
                            boxShadow: '0 24px 64px rgba(0, 0, 0, 0.8)'
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                            <strong style={{ color: '#00D4AA', fontSize: '16px' }}>
                              📷 Scan FitLens Invitation
                            </strong>
                            <button
                              onClick={() => setShowEnlargedQr(false)}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: '#a0aec0',
                                fontSize: '20px',
                                cursor: 'pointer',
                                padding: '4px 8px'
                              }}
                            >
                              ✕
                            </button>
                          </div>

                          <div style={{
                            padding: '24px',
                            backgroundColor: '#FFFFFF',
                            borderRadius: '20px',
                            display: 'inline-block',
                            boxShadow: '0 8px 30px rgba(0, 212, 170, 0.4)',
                            marginBottom: '18px'
                          }}>
                            <QRCodeSVG
                              value={inviteResult.claim_url}
                              size={280}
                              level="M"
                              includeMargin={true}
                              fgColor="#000000"
                              bgColor="#FFFFFF"
                            />
                          </div>

                          {inviteResult.invite_code && (
                            <div style={{
                              padding: '10px 16px',
                              backgroundColor: '#0a0e27',
                              borderRadius: '12px',
                              border: '1px dashed #2D3561',
                              marginBottom: '16px'
                            }}>
                              <span style={{ fontSize: '11px', color: '#a0aec0', textTransform: 'uppercase', letterSpacing: '1px', display: 'block' }}>
                                Or enter invitation code
                              </span>
                              <strong style={{ fontSize: '22px', color: '#00D4AA', letterSpacing: '2px', fontFamily: 'monospace' }}>
                                {inviteResult.invite_code}
                              </strong>
                            </div>
                          )}

                          <div style={{
                            padding: '10px 14px',
                            backgroundColor: 'rgba(0, 212, 170, 0.1)',
                            borderRadius: '10px',
                            fontSize: '12px',
                            color: '#e6fffa',
                            marginBottom: '20px',
                            lineHeight: '1.4'
                          }}>
                            💡 <strong>Tip:</strong> Turn up your phone screen brightness to maximum so the other phone camera can scan instantly without reflections.
                          </div>

                          <div style={{ display: 'flex', gap: '10px' }}>
                            <button
                              type="button"
                              onClick={handleShareInvite}
                              style={{
                                flex: 1,
                                padding: '12px',
                                backgroundColor: '#00D4AA',
                                border: 'none',
                                borderRadius: '10px',
                                color: '#0a0e27',
                                fontWeight: '700',
                                fontSize: '13px',
                                cursor: 'pointer'
                              }}
                            >
                              📤 Share Link
                            </button>
                            <button
                              type="button"
                              onClick={() => setShowEnlargedQr(false)}
                              style={{
                                padding: '12px 20px',
                                backgroundColor: '#1E2340',
                                border: '1px solid #2D3561',
                                borderRadius: '10px',
                                color: '#ffffff',
                                fontWeight: '600',
                                fontSize: '13px',
                                cursor: 'pointer'
                              }}
                            >
                              Close
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* 15-Minute Code Box */}
                    {inviteResult.invite_code && (
                      <div style={{
                        background: '#0a0e27',
                        border: '1px dashed #2D3561',
                        borderRadius: '12px',
                        padding: '14px 18px',
                        marginBottom: '16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        flexWrap: 'wrap',
                        gap: '10px'
                      }}>
                        <div>
                          <div style={{ fontSize: '11px', color: '#a0aec0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                            15-Minute Invite Code
                          </div>
                          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00D4AA', letterSpacing: '3px', fontFamily: 'monospace' }}>
                            {inviteResult.invite_code}
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleCopy(inviteResult.invite_code, 'code')}
                          style={{
                            padding: '10px 18px',
                            backgroundColor: copiedType === 'code' ? '#00D4AA' : '#1E2340',
                            border: '1px solid #2D3561',
                            borderRadius: '8px',
                            color: copiedType === 'code' ? '#0a0e27' : '#00D4AA',
                            fontWeight: '700',
                            fontSize: '13px',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease'
                          }}
                        >
                          {copiedType === 'code' ? '✓ Copied!' : '📋 Copy Invite Code'}
                        </button>
                      </div>
                    )}

                    {/* Link Actions */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '16px' }}>
                      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                        <button
                          type="button"
                          onClick={() => handleCopy(inviteResult.claim_url, 'claim_url')}
                          style={{
                            flex: 1,
                            minWidth: '160px',
                            padding: '12px 18px',
                            backgroundColor: copiedType === 'claim_url' ? '#00D4AA' : '#1E2340',
                            border: '1px solid #00D4AA',
                            borderRadius: '10px',
                            color: copiedType === 'claim_url' ? '#0a0e27' : '#00D4AA',
                            fontWeight: '700',
                            fontSize: '13px',
                            cursor: 'pointer',
                            textAlign: 'center',
                            transition: 'all 0.2s ease'
                          }}
                        >
                          {copiedType === 'claim_url' ? '✓ Claim Link Copied!' : '🔗 Copy Claim Link'}
                        </button>

                        <button
                          type="button"
                          onClick={handleShareInvite}
                          style={{
                            flex: 1,
                            minWidth: '160px',
                            padding: '12px 18px',
                            backgroundColor: '#00D4AA',
                            border: 'none',
                            borderRadius: '10px',
                            color: '#0a0e27',
                            fontWeight: '700',
                            fontSize: '13px',
                            cursor: 'pointer',
                            textAlign: 'center'
                          }}
                        >
                          📤 Share / Copy Claim Link
                        </button>
                      </div>

                      {inviteResult.mobile_invite_link && (
                        <div>
                          <div style={{ fontSize: '11px', color: '#00D4AA', marginBottom: '4px', fontWeight: '600' }}>
                            📱 Mobile / Same Wi-Fi Link (For Phones):
                          </div>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <input
                              type="text"
                              readOnly
                              value={inviteResult.mobile_invite_link}
                              style={{
                                flex: 1,
                                padding: '10px 12px',
                                backgroundColor: '#0a0e27',
                                border: '1px solid #2D3561',
                                borderRadius: '8px',
                                color: '#cbd5e0',
                                fontSize: '12px',
                                outline: 'none'
                              }}
                            />
                            <button
                              type="button"
                              onClick={() => handleCopy(inviteResult.mobile_invite_link, 'mobile_link')}
                              style={{
                                padding: '10px 16px',
                                backgroundColor: copiedType === 'mobile_link' ? '#2D3561' : '#00D4AA',
                                border: 'none',
                                borderRadius: '8px',
                                color: copiedType === 'mobile_link' ? '#00D4AA' : '#0a0e27',
                                fontWeight: '700',
                                fontSize: '12px',
                                cursor: 'pointer',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              {copiedType === 'mobile_link' ? '✓ Copied!' : '📱 Copy'}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid #1E2340', paddingTop: '14px' }}>
                      <button
                        type="button"
                        onClick={() => handleRevokeInvite(inviteResult.invite_id)}
                        style={{
                          background: 'none',
                          border: '1px solid #fc8181',
                          borderRadius: '8px',
                          color: '#fc8181',
                          padding: '6px 14px',
                          fontSize: '12px',
                          fontWeight: '600',
                          cursor: 'pointer'
                        }}
                      >
                        🗑️ Revoke Invite
                      </button>
                    </div>
                  </div>
                )}

                {/* 2. Pending invite after reload notice (only if active pending without fresh QR) */}
                {!inviteResult?.claim_url && pendingInvite && (
                  <div style={{
                    marginTop: '20px',
                    padding: '20px',
                    backgroundColor: '#131838',
                    border: '1px solid #ED8936',
                    borderRadius: '16px',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '28px', marginBottom: '6px' }}>⏱️</div>
                    <h4 style={{ color: '#ED8936', margin: '0 0 6px 0', fontSize: '15px', fontWeight: '700' }}>
                      Active Invitation in Progress ({pendingInvite.profile_name || pendingInvite.relationship || 'Member'})
                    </h4>
                    <p style={{ color: '#cbd5e0', fontSize: '12px', lineHeight: '1.5', maxWidth: '480px', margin: '0 auto 10px auto' }}>
                      Status: <strong style={{ color: '#00D4AA' }}>{pendingInvite.status_display || pendingInvite.status}</strong> • Invited Email: <strong style={{ color: '#00D4AA' }}>{pendingInvite.masked_email}</strong>
                    </p>
                    <div style={{
                      padding: '10px 14px',
                      backgroundColor: 'rgba(237, 137, 54, 0.1)',
                      border: '1px solid rgba(237, 137, 54, 0.3)',
                      borderRadius: '8px',
                      fontSize: '11px',
                      color: '#fed7aa',
                      lineHeight: '1.5',
                      maxWidth: '480px',
                      margin: '0 auto 12px auto',
                      textAlign: 'left'
                    }}>
                      🔒 <strong>Security Policy:</strong> Single-use invitation tokens are hashed and never stored in plain text. If your member needs a fresh link, revoke this invite to immediately generate a new one.
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRevokeInvite(pendingInvite.invite_id)}
                      style={{
                        padding: '10px 20px',
                        backgroundColor: 'rgba(252, 129, 129, 0.15)',
                        border: '1px solid #fc8181',
                        borderRadius: '8px',
                        color: '#fc8181',
                        fontWeight: '700',
                        fontSize: '13px',
                        cursor: 'pointer'
                      }}
                    >
                      🗑️ Revoke Invite
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* 3. OWNER IN-APP NOTIFICATIONS & VERIFICATION CONFIRMATIONS */}
            {isCurrentOwner && (
              <div style={{
                marginTop: '28px',
                backgroundColor: '#0a0e27',
                border: '1px solid #2D3561',
                borderRadius: '16px',
                padding: '24px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '20px' }}>🔔</span>
                    <div>
                      <h4 style={{ margin: 0, color: '#ffffff', fontSize: '16px', fontWeight: '800' }}>
                        Verified Invitation Confirmations
                      </h4>
                      <p style={{ margin: '2px 0 0', color: '#a0aec0', fontSize: '12px' }}>
                        Verifiable in-app confirmations when member invitations are claimed
                      </p>
                    </div>
                  </div>
                  {unreadCount > 0 && (
                    <span style={{
                      padding: '3px 10px',
                      backgroundColor: 'rgba(0, 212, 170, 0.15)',
                      border: '1px solid #00D4AA',
                      borderRadius: '12px',
                      color: '#00D4AA',
                      fontWeight: '800',
                      fontSize: '11px'
                    }}>
                      {unreadCount} UNREAD
                    </span>
                  )}
                </div>

                {notifications.length === 0 ? (
                  <p style={{ margin: 0, color: '#718096', fontSize: '13px', fontStyle: 'italic' }}>
                    No invitation confirmation alerts yet.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {notifications.map(notif => (
                      <div
                        key={notif.id}
                        style={{
                          backgroundColor: notif.read ? '#131838' : 'rgba(0, 212, 170, 0.08)',
                          border: `1px solid ${notif.read ? '#2D3561' : '#00D4AA'}`,
                          borderRadius: '12px',
                          padding: '12px 16px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: '12px',
                          flexWrap: 'wrap'
                        }}
                      >
                        <div style={{ flex: 1, minWidth: '240px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <strong style={{ color: '#ffffff', fontSize: '13px' }}>{notif.title}</strong>
                            <span style={{ color: '#a0aec0', fontSize: '11px' }}>• {formatDate(notif.created_at)}</span>
                          </div>
                          <div style={{ color: '#cbd5e0', fontSize: '12px', marginTop: '3px' }}>
                            {notif.message}
                          </div>
                        </div>
                        {!notif.read && (
                          <button
                            type="button"
                            onClick={() => handleMarkNotificationRead(notif.id)}
                            style={{
                              padding: '5px 12px',
                              backgroundColor: '#1E2340',
                              border: '1px solid #00D4AA',
                              color: '#00D4AA',
                              borderRadius: '8px',
                              fontSize: '11px',
                              fontWeight: '700',
                              cursor: 'pointer'
                            }}
                          >
                            Mark Read ✓
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* 4. OWNER INVITATIONS & AUDIT TABLE */}
            {isCurrentOwner && (
              <div style={{
                marginTop: '28px',
                backgroundColor: '#0a0e27',
                border: '1px solid #2D3561',
                borderRadius: '16px',
                padding: '24px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '20px' }}>📋</span>
                    <div>
                      <h4 style={{ margin: 0, color: '#00D4AA', fontSize: '16px', fontWeight: '800' }}>
                        Invitation Audit & Status
                      </h4>
                      <p style={{ margin: '2px 0 0', color: '#a0aec0', fontSize: '12px' }}>
                        Verifiable audit trail: Sent, Opened, Verification Pending, Accepted, Expired, Revoked
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={fetchProfilesList}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#1E2340',
                      border: '1px solid #2D3561',
                      borderRadius: '8px',
                      color: '#00D4AA',
                      fontSize: '12px',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    🔄 Refresh Audit
                  </button>
                </div>

                {invitesList.length === 0 ? (
                  <p style={{ margin: 0, color: '#718096', fontSize: '13px', fontStyle: 'italic' }}>
                    No invitations have been created for this account yet.
                  </p>
                ) : (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid #2D3561', color: '#a0aec0', textTransform: 'uppercase', fontSize: '11px', letterSpacing: '0.5px' }}>
                          <th style={{ padding: '10px 12px' }}>Profile Display Name</th>
                          <th style={{ padding: '10px 12px' }}>Invite State</th>
                          <th style={{ padding: '10px 12px' }}>Masked Email</th>
                          <th style={{ padding: '10px 12px' }}>Sent Date/Time</th>
                          <th style={{ padding: '10px 12px' }}>Opened Date/Time</th>
                          <th style={{ padding: '10px 12px' }}>Accepted Date/Time</th>
                          <th style={{ padding: '10px 12px' }}>Last Active</th>
                          <th style={{ padding: '10px 12px', textAlign: 'right' }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {invitesList.map(inv => {
                          const isActive = ['sent', 'opened', 'verification_pending', 'pending'].includes(inv.status);
                          return (
                            <tr key={inv.invite_id || inv.id} style={{ borderBottom: '1px solid rgba(45, 53, 97, 0.4)' }}>
                              <td style={{ padding: '12px', fontWeight: '700', color: '#ffffff' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                  <span>{inv.profile_name || 'Member Profile'}</span>
                                  {inv.relationship && (
                                    <span style={{ fontSize: '10px', backgroundColor: '#1E2340', color: '#a0aec0', padding: '1px 6px', borderRadius: '4px' }}>
                                      {inv.relationship}
                                    </span>
                                  )}
                                </div>
                              </td>
                              <td style={{ padding: '12px' }}>
                                {renderStatusBadge(inv.status_display, inv.status)}
                              </td>
                              <td style={{ padding: '12px', color: '#00D4AA', fontFamily: 'monospace' }}>
                                {inv.masked_email || '—'}
                              </td>
                              <td style={{ padding: '12px', color: '#cbd5e0' }}>
                                {formatDate(inv.created_at || inv.sent_at)}
                              </td>
                              <td style={{ padding: '12px', color: inv.opened_at ? '#FBBF24' : '#718096' }}>
                                {formatDate(inv.opened_at)}
                              </td>
                              <td style={{ padding: '12px', color: inv.claimed_at ? '#34D399' : '#718096' }}>
                                {formatDate(inv.claimed_at)}
                              </td>
                              <td style={{ padding: '12px', color: '#cbd5e0' }}>
                                {formatDate(inv.last_active_at)}
                              </td>
                              <td style={{ padding: '12px', textAlign: 'right' }}>
                                {isActive ? (
                                  <button
                                    type="button"
                                    onClick={() => handleRevokeInvite(inv.invite_id || inv.id)}
                                    style={{
                                      padding: '4px 10px',
                                      backgroundColor: 'rgba(239, 68, 68, 0.15)',
                                      border: '1px solid #EF4444',
                                      color: '#F87171',
                                      borderRadius: '6px',
                                      fontSize: '11px',
                                      fontWeight: '700',
                                      cursor: 'pointer'
                                    }}
                                  >
                                    Revoke
                                  </button>
                                ) : inv.status === 'claimed' ? (
                                  <span style={{ color: '#10B981', fontWeight: '700', fontSize: '11px' }}>✓ Claimed</span>
                                ) : (
                                  <span style={{ color: '#718096', fontSize: '11px' }}>Inactive</span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}

                <div style={{
                  marginTop: '16px',
                  padding: '12px 14px',
                  backgroundColor: '#131838',
                  border: '1px solid #2D3561',
                  borderRadius: '10px',
                  color: '#a0aec0',
                  fontSize: '11px',
                  lineHeight: '1.5'
                }}>
                  🔒 <strong>Privacy Isolation Guarantee:</strong> Non-owner member measurements, photos, 3D mesh models, scan histories, OTP values, and raw IP addresses are strictly isolated and never exposed in this dashboard.
                </div>
              </div>
            )}
          </div>
        );
      })()}

        {/* Tab 3: Security */}
        {activeTab === 'security' && (
          <div>
            <h3 style={{ marginTop: 0, color: '#ffffff' }}>Change Password</h3>
            <form onSubmit={handleChangePassword} style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '450px' }}>
              <div>
                <label style={{ display: 'block', color: '#a0aec0', fontSize: '13px', marginBottom: '8px' }}>
                  Current Password
                </label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '10px',
                    color: '#ffffff',
                    fontSize: '15px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', color: '#a0aec0', fontSize: '13px', marginBottom: '8px' }}>
                  New Password (min 8 chars, 1 number)
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '10px',
                    color: '#ffffff',
                    fontSize: '15px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', color: '#a0aec0', fontSize: '13px', marginBottom: '8px' }}>
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '10px',
                    color: '#ffffff',
                    fontSize: '15px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={securityLoading}
                style={{
                  width: 'fit-content',
                  padding: '12px 28px',
                  backgroundColor: '#00D4AA',
                  border: 'none',
                  borderRadius: '10px',
                  color: '#0a0e27',
                  fontWeight: '700',
                  cursor: securityLoading ? 'wait' : 'pointer'
                }}
              >
                {securityLoading ? 'Updating...' : 'Update Password'}
              </button>
            </form>
          </div>
        )}

        {/* Tab 3: History */}
        {activeTab === 'history' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0 }}>Measurement History</h3>
              <button
                onClick={fetchHistory}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#0a0e27',
                  border: '1px solid #2D3561',
                  borderRadius: '8px',
                  color: '#00D4AA',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
              >
                🔄 Refresh
              </button>
            </div>

            {historyLoading ? (
              <p style={{ color: '#a0aec0' }}>Loading scan history...</p>
            ) : history.length === 0 ? (
              <p style={{ color: '#a0aec0' }}>No scan records found.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {history.map((scan) => (
                  <div key={scan.analysis_id} style={{
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '14px',
                    padding: '18px 22px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ color: '#00D4AA', fontWeight: '800', fontSize: '15px' }}>
                          ID: {scan.analysis_id}
                        </span>
                        <span style={{ color: '#a0aec0', fontSize: '13px' }}>
                          • {scan.date || 'Recent'}
                        </span>
                      </div>
                      <div style={{ color: '#e2e8f0', fontSize: '13px', marginTop: '6px' }}>
                        Height: {scan.height_cm ? `${scan.height_cm} cm` : 'N/A'} | Chest: {scan.chest_circumference ? `${scan.chest_circumference} cm` : 'N/A'} | Waist: {scan.waist_circumference ? `${scan.waist_circumference} cm` : 'N/A'}
                      </div>
                    </div>

                    <button
                      onClick={() => handleDeleteScan(scan.analysis_id)}
                      style={{
                        backgroundColor: 'rgba(252, 129, 129, 0.15)',
                        border: '1px solid #fc8181',
                        color: '#fc8181',
                        padding: '8px 14px',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        fontWeight: '600',
                        fontSize: '13px'
                      }}
                    >
                      🗑️ Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Account */}
        {activeTab === 'account' && (
          <div>
            <h3 style={{ marginTop: 0 }}>Account Overview</h3>
            <div style={{
              backgroundColor: '#0a0e27',
              border: '1px solid #2D3561',
              borderRadius: '14px',
              padding: '20px',
              marginBottom: '28px',
              display: 'flex',
              gap: '40px'
            }}>
              <div>
                <span style={{ color: '#a0aec0', fontSize: '13px' }}>User ID</span>
                <p style={{ margin: '4px 0 0 0', fontWeight: '700', color: '#00D4AA' }}>{user?.user_id || 'N/A'}</p>
              </div>
              <div>
                <span style={{ color: '#a0aec0', fontSize: '13px' }}>Saved Scans</span>
                <p style={{ margin: '4px 0 0 0', fontWeight: '700', color: '#ffffff' }}>{history.length} scans</p>
              </div>
            </div>

            <div style={{
              border: '1px solid rgba(252, 129, 129, 0.4)',
              backgroundColor: 'rgba(252, 129, 129, 0.05)',
              borderRadius: '16px',
              padding: '24px'
            }}>
              <h4 style={{ margin: '0 0 8px 0', color: '#fc8181', fontSize: '16px' }}>⚠️ Danger Zone</h4>
              <p style={{ color: '#a0aec0', fontSize: '14px', margin: '0 0 16px 0' }}>
                Deleting your account will permanently wipe all measurement history and data. This action cannot be undone.
              </p>
              <button
                onClick={() => setShowDeleteModal(true)}
                style={{
                  padding: '12px 24px',
                  backgroundColor: '#fc8181',
                  border: 'none',
                  borderRadius: '10px',
                  color: '#0a0e27',
                  fontWeight: '700',
                  cursor: 'pointer'
                }}
              >
                Delete Account
              </button>
            </div>
          </div>
        )}

        {/* Tab 5: About */}
        {activeTab === 'about' && (
          <div style={{ lineHeight: '1.6' }}>
            <h3 style={{ marginTop: 0 }}>FitLens AI System</h3>
            <p style={{ color: '#a0aec0', fontSize: '14px' }}>
              FitLens is a cutting-edge 3D Body Measurement application leveraging YOLOv8 Segmentation, MediaPipe Landmark detection, and SMPL 3D Mesh modeling for instant body analytics.
            </p>

            <div style={{
              backgroundColor: '#0a0e27',
              border: '1px solid #2D3561',
              borderRadius: '14px',
              padding: '20px',
              marginTop: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
              fontSize: '14px'
            }}>
              <div><strong>App Version:</strong> 1.0.0</div>
              <div><strong>Institution:</strong> REVA University</div>
              <div><strong>Faculty Guide:</strong> Dr. Argha Sarkar</div>
              <div><strong>Contact:</strong> support@fitlens.app</div>
            </div>
          </div>
        )}
      </div>

      {/* Delete Account Modal */}
      {showDeleteModal && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(10, 14, 39, 0.85)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          backdropFilter: 'blur(6px)'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '400px',
            backgroundColor: '#1E2340',
            border: '1px solid #fc8181',
            borderRadius: '20px',
            padding: '28px'
          }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#fc8181' }}>Confirm Account Deletion</h3>
            <p style={{ color: '#a0aec0', fontSize: '13px', marginBottom: '20px' }}>
              To confirm account deletion, please enter your password.
            </p>
            <form onSubmit={handleDeleteAccount} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <input
                type="password"
                placeholder="Enter your password"
                value={deletePassword}
                onChange={(e) => setDeletePassword(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  backgroundColor: '#0a0e27',
                  border: '1px solid #2D3561',
                  borderRadius: '10px',
                  color: '#ffffff',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowDeleteModal(false)}
                  style={{
                    flex: 1,
                    padding: '10px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '8px',
                    color: '#a0aec0',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={deleteLoading}
                  style={{
                    flex: 1,
                    padding: '10px',
                    backgroundColor: '#fc8181',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#0a0e27',
                    fontWeight: '700',
                    cursor: deleteLoading ? 'wait' : 'pointer'
                  }}
                >
                  {deleteLoading ? 'Deleting...' : 'Confirm Delete'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Profile Modal */}
      {editingProfile && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(10, 14, 39, 0.85)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          backdropFilter: 'blur(6px)'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '420px',
            backgroundColor: '#1E2340',
            border: '1px solid #00D4AA',
            borderRadius: '20px',
            padding: '28px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
            color: '#ffffff'
          }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#ffffff', fontSize: '18px', fontWeight: '800' }}>
              ✏️ Edit Profile: {editingProfile.name}
            </h3>
            <form onSubmit={handleSaveEdit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', color: '#a0aec0', fontSize: '12px', fontWeight: '700', marginBottom: '6px' }}>
                  PROFILE NAME
                </label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '10px',
                    color: '#ffffff',
                    fontSize: '14px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', color: '#a0aec0', fontSize: '12px', fontWeight: '700', marginBottom: '6px' }}>
                  DEFAULT HEIGHT (CM)
                </label>
                <input
                  type="number"
                  min="100"
                  max="250"
                  step="0.5"
                  value={editHeight}
                  onChange={(e) => setEditHeight(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '10px',
                    color: '#ffffff',
                    fontSize: '14px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => setEditingProfile(null)}
                  style={{
                    flex: 1,
                    padding: '10px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '8px',
                    color: '#a0aec0',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editLoading}
                  style={{
                    flex: 1,
                    padding: '10px',
                    backgroundColor: '#00D4AA',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#0a0e27',
                    fontWeight: '700',
                    cursor: editLoading ? 'wait' : 'pointer'
                  }}
                >
                  {editLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
