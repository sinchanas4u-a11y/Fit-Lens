import React, { useState, useEffect } from 'react';
import { profileService } from '../services/profileService';
import { getAccessMode } from '../services/authService';
import logo from '../assets/logo.png';

export default function ProfileSelectionModal({
  isOpen,
  profiles = [],
  user,
  initialMemberEmail = '',
  onSelectProfile,
  onLogout
}) {
  const [unlockedProfileId, setUnlockedProfileId] = useState(() => profileService.getUnlockedProfileId());
  const [memberEmail, setMemberEmail] = useState(() => initialMemberEmail || localStorage.getItem('fitlens_member_email') || '');
  const [unlockLoading, setUnlockLoading] = useState(false);
  const [unlockError, setUnlockError] = useState(null);
  const [unlockSuccess, setUnlockSuccess] = useState(null);

  // Owner unlock password modal state
  const [showOwnerPasswordModal, setShowOwnerPasswordModal] = useState(false);
  const [ownerPassword, setOwnerPassword] = useState('');
  const [ownerLoading, setOwnerLoading] = useState(false);
  const [ownerError, setOwnerError] = useState(null);

  // Auto-attempt unlock if initial member email is present on open
  useEffect(() => {
    if (isOpen) {
      if (initialMemberEmail) {
        setMemberEmail(initialMemberEmail);
      }
      const emailToUse = initialMemberEmail || memberEmail;
      if (emailToUse && !unlockedProfileId) {
        handleUnlockByEmail(emailToUse);
      }
    }
  }, [isOpen, initialMemberEmail]);

  if (!isOpen || getAccessMode() === 'invited_profile') return null;

  const handleUnlockByEmail = async (emailToUnlock) => {
    const trimmed = (emailToUnlock || memberEmail).trim().toLowerCase();
    if (!trimmed) {
      setUnlockError('Please enter the email address where your invitation was sent.');
      return;
    }

    if (!trimmed.includes('@') || !trimmed.includes('.')) {
      setUnlockError('Please enter a valid email address.');
      return;
    }

    setUnlockLoading(true);
    setUnlockError(null);
    setUnlockSuccess(null);

    try {
      const res = await profileService.unlockInvitedProfile(trimmed);
      if (res.success && res.profile) {
        const pid = String(res.profile.profile_id || res.profile.id);
        setUnlockedProfileId(pid);
        profileService.saveUnlockedProfileId(pid);
        profileService.saveActiveProfile(res.profile);
        localStorage.setItem('fitlens_member_email', trimmed);
        setUnlockSuccess(`✅ Profile unlocked for "${res.profile?.name || 'Member'}"! Opening your personal measurement space...`);
        setTimeout(() => {
          if (onSelectProfile) onSelectProfile(res.profile);
        }, 600);
      } else {
        setUnlockError(res.error || 'No matching active invitation found for this email address.');
      }
    } catch (err) {
      setUnlockError(err.message || 'Error connecting to profile unlock service.');
    } finally {
      setUnlockLoading(false);
    }
  };

  const handleOwnerUnlockSubmit = async (e) => {
    e.preventDefault();
    setOwnerLoading(true);
    setOwnerError(null);

    try {
      const res = await profileService.unlockOwnerProfile(ownerPassword || null);

      if (res.success && res.profile) {
        const pid = String(res.profile.profile_id || res.profile.id);
        setUnlockedProfileId(pid);
        profileService.saveUnlockedProfileId(pid);
        profileService.saveActiveProfile(res.profile);
        setShowOwnerPasswordModal(false);
        setOwnerPassword('');
        setUnlockSuccess('👑 Account Owner Profile unlocked! Opening your measurement space...');
        setTimeout(() => {
          if (onSelectProfile) onSelectProfile(res.profile);
        }, 600);
      } else {
        setOwnerError(res.error || 'Authentication failed. Please verify your password.');
      }
    } catch (err) {
      setOwnerError(err.message || 'Error unlocking owner profile.');
    } finally {
      setOwnerLoading(false);
    }
  };

  const handleCardClick = (profile) => {
    const pId = String(profile.id || profile.profile_id || profile._id);
    const isUnlocked = unlockedProfileId === pId;

    if (isUnlocked) {
      profileService.saveActiveProfile(profile);
      if (onSelectProfile) onSelectProfile(profile);
      return;
    }

    if (unlockedProfileId) {
      const unlockedProfile = profiles.find(p => String(p.id || p.profile_id || p._id) === String(unlockedProfileId));
      setUnlockError(
        `🔒 Profile Locked: Only your unlocked profile ("${unlockedProfile?.name || 'My Profile'}") is accessible. Switching to other profiles is disabled.`
      );
      return;
    }

    if (profile.is_owner || profile.profile_type === 'owner') {
      setShowOwnerPasswordModal(true);
    } else {
      setUnlockError(
        `🔒 "${profile.name}" is locked. Enter the email address this invitation was sent to in the box above to unlock it.`
      );
    }
  };

  // Determine which profiles to render
  const accessMode = getAccessMode();
  const visibleProfiles = profiles.filter((p) => {
    const pId = String(p.id || p.profile_id || p._id);
    if (unlockedProfileId && accessMode === 'invited_profile') {
      // Do not expose owner profile or other profiles to invited member
      return pId === String(unlockedProfileId);
    }
    return true;
  });

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(10, 14, 39, 0.94)',
      backdropFilter: 'blur(12px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000,
      padding: '20px',
      overflowY: 'auto'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '720px',
        backgroundColor: '#1E2340',
        borderRadius: '24px',
        border: '1px solid #2D3561',
        padding: '36px',
        boxShadow: '0 24px 64px rgba(0, 0, 0, 0.6)',
        color: '#ffffff',
        fontFamily: 'Inter, system-ui, sans-serif'
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <img src={logo} alt="FitLens Logo" style={{ height: '70px', objectFit: 'contain', marginBottom: '12px' }} />
          <h2 style={{ fontSize: '26px', fontWeight: '800', margin: '0 0 6px 0', color: '#ffffff' }}>
            👥 Available Profiles
          </h2>
          <p style={{ color: '#a0aec0', fontSize: '14px', margin: 0 }}>
            Choose your profile to access your body measurements and scans. Invited members can unlock only the profile linked to their invitation.
          </p>
        </div>

        {/* Alerts */}
        {unlockSuccess && (
          <div style={{
            backgroundColor: 'rgba(0, 212, 170, 0.15)',
            border: '1px solid #00D4AA',
            color: '#00D4AA',
            borderRadius: '12px',
            padding: '12px 18px',
            fontSize: '14px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            {unlockSuccess}
          </div>
        )}

        {unlockError && (
          <div style={{
            backgroundColor: 'rgba(252, 129, 129, 0.15)',
            border: '1px solid #fc8181',
            color: '#fc8181',
            borderRadius: '12px',
            padding: '12px 18px',
            fontSize: '14px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            ⚠️ {unlockError}
          </div>
        )}

        {/* Member Email Unlock Section */}
        <div style={{
          backgroundColor: '#131838',
          border: '1px solid #2D3561',
          borderRadius: '16px',
          padding: '20px',
          marginBottom: '28px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span style={{ fontSize: '20px' }}>✉️</span>
            <strong style={{ fontSize: '15px', color: '#00D4AA' }}>Invited Member Unlock</strong>
          </div>
          <p style={{ color: '#a0aec0', fontSize: '13px', margin: '0 0 14px 0', lineHeight: '1.5' }}>
            Enter the email address to which your invitation was sent. Only your assigned profile will be unlocked; all other profiles remain locked.
          </p>

          <form onSubmit={(e) => { e.preventDefault(); handleUnlockByEmail(); }} style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <input
              type="email"
              value={memberEmail}
              onChange={(e) => setMemberEmail(e.target.value)}
              placeholder="e.g. member@example.com"
              required
              style={{
                flex: 1,
                minWidth: '220px',
                padding: '12px 16px',
                backgroundColor: '#0a0e27',
                border: '1px solid #2D3561',
                borderRadius: '10px',
                color: '#ffffff',
                fontSize: '14px',
                outline: 'none'
              }}
            />
            <button
              type="submit"
              disabled={unlockLoading}
              style={{
                padding: '12px 24px',
                backgroundColor: '#00D4AA',
                color: '#0a0e27',
                border: 'none',
                borderRadius: '10px',
                fontWeight: '700',
                fontSize: '14px',
                cursor: unlockLoading ? 'wait' : 'pointer',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap'
              }}
            >
              {unlockLoading ? 'Unlocking...' : 'Unlock Profile 🔓'}
            </button>
          </form>

          {/* Owner Unlock Section */}
          <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid #1E2340', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <span style={{ fontSize: '12px', color: '#718096' }}>
              Are you the Account Owner ({user?.name || 'Owner'})?
            </span>
            <button
              type="button"
              onClick={() => setShowOwnerPasswordModal(true)}
              style={{
                background: 'none',
                border: '1px solid rgba(0, 212, 170, 0.4)',
                color: '#00D4AA',
                padding: '4px 12px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              Unlock Owner Profile 👑
            </button>
          </div>
        </div>

        {/* Profiles Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '28px'
        }}>
          {visibleProfiles.map((p) => {
            const pId = String(p.id || p.profile_id || p._id);
            const isUnlocked = unlockedProfileId === pId;

            return (
              <div
                key={pId}
                onClick={() => handleCardClick(p)}
                style={{
                  backgroundColor: isUnlocked ? 'rgba(0, 212, 170, 0.08)' : '#131838',
                  border: isUnlocked ? '2px solid #00D4AA' : '1px solid #2D3561',
                  borderRadius: '16px',
                  padding: '20px 16px',
                  textAlign: 'center',
                  cursor: isUnlocked ? 'pointer' : 'default',
                  opacity: isUnlocked ? 1 : (unlockedProfileId ? 0.45 : 0.85),
                  boxShadow: isUnlocked ? '0 0 24px rgba(0, 212, 170, 0.35)' : 'none',
                  transition: 'all 0.25s ease',
                  position: 'relative'
                }}
              >
                {/* Lock / Unlock Tag Badge */}
                <div style={{
                  position: 'absolute',
                  top: '12px',
                  right: '12px',
                  padding: '3px 8px',
                  borderRadius: '10px',
                  fontSize: '11px',
                  fontWeight: '700',
                  backgroundColor: isUnlocked ? 'rgba(0, 212, 170, 0.2)' : 'rgba(252, 129, 129, 0.2)',
                  color: isUnlocked ? '#00D4AA' : '#fc8181',
                  border: `1px solid ${isUnlocked ? '#00D4AA' : '#fc8181'}`
                }}>
                  {isUnlocked ? '🔓 Unlocked' : '🔒 Locked'}
                </div>

                {/* Avatar */}
                <div style={{
                  width: '54px',
                  height: '54px',
                  borderRadius: '50%',
                  background: isUnlocked
                    ? 'linear-gradient(135deg, #00D4AA, #0080FF)'
                    : (p.is_owner ? 'linear-gradient(135deg, #FFB300, #FF7043)' : '#2D3561'),
                  color: isUnlocked ? '#0a0e27' : '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: '800',
                  fontSize: '22px',
                  margin: '0 auto 12px auto'
                }}>
                  {(p.name || 'U').charAt(0).toUpperCase()}
                </div>

                {/* Name */}
                <h4 style={{ margin: '0 0 6px 0', fontSize: '16px', fontWeight: '700', color: '#ffffff' }}>
                  {p.name}
                </h4>

                {/* Role Pill */}
                <span style={{
                  display: 'inline-block',
                  fontSize: '11px',
                  backgroundColor: p.is_owner ? 'rgba(0, 212, 170, 0.2)' : 'rgba(160, 174, 192, 0.15)',
                  color: p.is_owner ? '#00D4AA' : '#a0aec0',
                  padding: '2px 8px',
                  borderRadius: '10px',
                  fontWeight: '700',
                  marginBottom: '10px'
                }}>
                  {p.is_owner ? '👑 Owner' : (p.relationship || 'Member')}
                </span>

                <div style={{ fontSize: '12px', color: '#718096', marginBottom: '14px' }}>
                  Status: <strong style={{ color: '#cbd5e0' }}>{p.status || (p.is_archived ? 'Archived' : 'Active')}</strong>
                </div>

                {/* Action button */}
                {isUnlocked ? (
                  <button
                    type="button"
                    style={{
                      width: '100%',
                      padding: '10px',
                      backgroundColor: '#00D4AA',
                      color: '#0a0e27',
                      border: 'none',
                      borderRadius: '10px',
                      fontWeight: '800',
                      fontSize: '13px',
                      cursor: 'pointer'
                    }}
                  >
                    Enter Profile ➔
                  </button>
                ) : (
                  <div style={{
                    fontSize: '12px',
                    color: '#718096',
                    padding: '8px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(255, 255, 255, 0.03)'
                  }}>
                    {unlockedProfileId ? 'Access Restricted' : 'Enter email to unlock'}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer Logout */}
        <div style={{ textAlign: 'center', borderTop: '1px solid #2D3561', paddingTop: '20px' }}>
          <button
            type="button"
            onClick={onLogout}
            style={{
              background: 'none',
              border: 'none',
              color: '#fc8181',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            Log Out of Account 🚪
          </button>
        </div>
      </div>

      {/* Owner Password Verification Modal */}
      {showOwnerPasswordModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2100,
          padding: '20px'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '380px',
            backgroundColor: '#1E2340',
            border: '1px solid #00D4AA',
            borderRadius: '20px',
            padding: '28px',
            boxShadow: '0 20px 48px rgba(0, 0, 0, 0.7)'
          }}>
            <h3 style={{ margin: '0 0 8px 0', color: '#ffffff', fontSize: '18px', fontWeight: '700' }}>
              👑 Owner Profile Unlock
            </h3>
            <p style={{ color: '#a0aec0', fontSize: '13px', margin: '0 0 16px 0', lineHeight: '1.5' }}>
              Confirm your owner account credentials to unlock the Owner profile.
            </p>

            {ownerError && (
              <div style={{
                backgroundColor: 'rgba(252, 129, 129, 0.15)',
                border: '1px solid #fc8181',
                color: '#fc8181',
                borderRadius: '8px',
                padding: '8px 12px',
                fontSize: '12px',
                marginBottom: '14px'
              }}>
                {ownerError}
              </div>
            )}

            <form onSubmit={handleOwnerUnlockSubmit}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', color: '#a0aec0', fontSize: '12px', marginBottom: '6px' }}>
                  Owner Password
                </label>
                <input
                  type="password"
                  value={ownerPassword}
                  onChange={(e) => setOwnerPassword(e.target.value)}
                  placeholder="Enter owner account password"
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '8px',
                    color: '#ffffff',
                    fontSize: '13px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => {
                    setShowOwnerPasswordModal(false);
                    setOwnerPassword('');
                    setOwnerError(null);
                  }}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'transparent',
                    border: '1px solid #2D3561',
                    color: '#a0aec0',
                    borderRadius: '8px',
                    fontSize: '13px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={ownerLoading}
                  style={{
                    padding: '8px 18px',
                    backgroundColor: '#00D4AA',
                    color: '#0a0e27',
                    border: 'none',
                    borderRadius: '8px',
                    fontWeight: '700',
                    fontSize: '13px',
                    cursor: ownerLoading ? 'wait' : 'pointer'
                  }}
                >
                  {ownerLoading ? 'Verifying...' : 'Unlock Owner'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
