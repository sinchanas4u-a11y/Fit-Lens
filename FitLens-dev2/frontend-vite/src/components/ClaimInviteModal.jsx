import React, { useState } from 'react';
import { profileService } from '../services/profileService';

export default function ClaimInviteModal({ initialCode = '', onClose, onClaimSuccess }) {
  const [inviteCode, setInviteCode] = useState(initialCode);
  const [name, setName] = useState('');
  const [heightCm, setHeightCm] = useState('170');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [claimedProfile, setClaimedProfile] = useState(null);

  const handleClaim = async (e) => {
    e.preventDefault();
    setError(null);

    const trimmedCode = inviteCode.trim().toUpperCase();
    if (!trimmedCode) {
      setError('Please enter your 6-character invitation code.');
      return;
    }

    const trimmedName = name.trim();
    if (!trimmedName || trimmedName.length < 1 || trimmedName.length > 50) {
      setError('Please enter your name (between 1 and 50 characters).');
      return;
    }

    const parsedHeight = parseFloat(heightCm);
    if (isNaN(parsedHeight) || parsedHeight < 100 || parsedHeight > 250) {
      setError('Please enter a valid height between 100 cm and 250 cm.');
      return;
    }

    setLoading(true);
    try {
      const res = await profileService.claimInvite({
        invite_code: trimmedCode,
        name: trimmedName,
        default_height_cm: parsedHeight
      });

      if (res.success) {
        setClaimedProfile(res.profile || { name: trimmedName });
        if (onClaimSuccess) onClaimSuccess(res);
      } else {
        const errMsg = res.error || 'Failed to claim invitation. Code may be invalid or expired.';
        const isAlreadyClaimed = errMsg.toLowerCase().includes('already been used') ||
                                 errMsg.toLowerCase().includes('already been accepted') ||
                                 errMsg.toLowerCase().includes('already been claimed');

        if (isAlreadyClaimed) {
          const activeProf = profileService.getActiveProfile();
          if (activeProf && (activeProf.name || activeProf.id || activeProf.profile_id)) {
            setClaimedProfile(activeProf);
            if (onClaimSuccess) onClaimSuccess({ success: true, profile: activeProf });
            return;
          }
        }
        setError(errMsg);
      }
    } catch (err) {
      setError(err.message || 'Error claiming invitation code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(10, 14, 39, 0.85)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1100,
      backdropFilter: 'blur(8px)',
      padding: '20px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '440px',
        backgroundColor: '#1E2340',
        border: '1px solid #2D3561',
        borderRadius: '20px',
        padding: '30px',
        boxShadow: '0 24px 48px rgba(0, 0, 0, 0.5)',
        position: 'relative'
      }}>
        {!claimedProfile ? (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '24px' }}>🎟️</span>
                <h3 style={{ margin: 0, color: '#ffffff', fontSize: '20px', fontWeight: '700' }}>
                  Join FitLens Account
                </h3>
              </div>
              <button
                type="button"
                onClick={onClose}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#a0aec0',
                  fontSize: '20px',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                ✕
              </button>
            </div>

            <p style={{ color: '#a0aec0', fontSize: '13px', lineHeight: '1.5', margin: '0 0 20px 0' }}>
              An account owner has invited you to create your own FitLens profile. Your measurements, photos, and scans will remain separate.
            </p>

            {error && (
              <div style={{
                padding: '12px 16px',
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid #EF4444',
                borderRadius: '10px',
                color: '#F87171',
                fontSize: '13px',
                marginBottom: '18px'
              }}>
                <div>⚠️ {error}</div>
                {profileService.getActiveProfile() && (
                  <button
                    type="button"
                    onClick={() => {
                      const p = profileService.getActiveProfile();
                      if (onClaimSuccess) onClaimSuccess({ success: true, profile: p });
                      if (onClose) onClose();
                    }}
                    style={{
                      marginTop: '10px',
                      padding: '10px 14px',
                      backgroundColor: '#00D4AA',
                      border: 'none',
                      borderRadius: '8px',
                      color: '#0a0e27',
                      fontWeight: '700',
                      fontSize: '13px',
                      cursor: 'pointer',
                      width: '100%'
                    }}
                  >
                    Enter My Profile ({profileService.getActiveProfile().name || 'Member'})
                  </button>
                )}
              </div>
            )}

            <form onSubmit={handleClaim} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', color: '#cbd5e0', fontSize: '12px', fontWeight: '600', marginBottom: '6px' }}>
                  INVITATION CODE
                </label>
                <input
                  type="text"
                  placeholder="e.g. A3F92C"
                  value={inviteCode}
                  onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
                  maxLength={12}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '10px',
                    color: '#00D4AA',
                    fontSize: '18px',
                    fontWeight: 'bold',
                    letterSpacing: '3px',
                    fontFamily: 'monospace',
                    boxSizing: 'border-box',
                    outline: 'none'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', color: '#cbd5e0', fontSize: '12px', fontWeight: '600', marginBottom: '6px' }}>
                  YOUR FULL NAME
                </label>
                <input
                  type="text"
                  placeholder="e.g. Jane Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={50}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '10px',
                    color: '#ffffff',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                    outline: 'none'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', color: '#cbd5e0', fontSize: '12px', fontWeight: '600', marginBottom: '6px' }}>
                  DEFAULT HEIGHT (CM)
                </label>
                <input
                  type="number"
                  placeholder="170"
                  value={heightCm}
                  onChange={(e) => setHeightCm(e.target.value)}
                  min="100"
                  max="250"
                  required
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '10px',
                    color: '#ffffff',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                    outline: 'none'
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '12px', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={onClose}
                  style={{
                    flex: 1,
                    padding: '12px',
                    backgroundColor: '#0a0e27',
                    border: '1px solid #2D3561',
                    borderRadius: '10px',
                    color: '#a0aec0',
                    fontWeight: '600',
                    fontSize: '14px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    flex: 2,
                    padding: '12px',
                    backgroundColor: '#00D4AA',
                    border: 'none',
                    borderRadius: '10px',
                    color: '#0a0e27',
                    fontWeight: '700',
                    fontSize: '14px',
                    cursor: loading ? 'wait' : 'pointer'
                  }}
                >
                  {loading ? 'Claiming Profile...' : 'Claim My Profile'}
                </button>
              </div>
            </form>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '10px 0' }}>
            <div style={{ fontSize: '48px', marginBottom: '14px' }}>🎉</div>
            <h3 style={{ color: '#00D4AA', margin: '0 0 10px 0', fontSize: '22px' }}>
              Profile Created!
            </h3>
            <p style={{ color: '#cbd5e0', fontSize: '14px', lineHeight: '1.6', marginBottom: '22px' }}>
              Welcome <strong style={{ color: '#ffffff' }}>{claimedProfile.name}</strong>! Your FitLens profile is now active under the family account.
              Measurements and scans taken under this profile will be preserved independently.
            </p>
            <button
              type="button"
              onClick={onClose}
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: '#00D4AA',
                border: 'none',
                borderRadius: '10px',
                color: '#0a0e27',
                fontWeight: '700',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              Continue to FitLens
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
