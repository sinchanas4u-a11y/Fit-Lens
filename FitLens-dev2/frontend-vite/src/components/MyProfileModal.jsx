import React, { useState, useEffect } from 'react';
import { profileService } from '../services/profileService';

export default function MyProfileModal({
  isOpen,
  activeProfile,
  onProfileUpdated,
  onClose
}) {
  const [displayName, setDisplayName] = useState('');
  const [heightCm, setHeightCm] = useState('170');
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setError(null);
      setSuccess(null);
      const initialName = activeProfile?.display_name || activeProfile?.name || '';
      const initialHeight = activeProfile?.height_cm || activeProfile?.default_height_cm || 170;
      setDisplayName(initialName);
      setHeightCm(String(initialHeight));

      // Fetch fresh server personal details
      let isMounted = true;
      setFetching(true);
      profileService.getMyPersonalDetails()
        .then((res) => {
          if (isMounted && res?.success && res?.profile) {
            if (res.profile.display_name) {
              setDisplayName(res.profile.display_name);
            }
            if (res.profile.height_cm) {
              setHeightCm(String(res.profile.height_cm));
            }
          }
        })
        .catch(() => {})
        .finally(() => {
          if (isMounted) setFetching(false);
        });

      return () => {
        isMounted = false;
      };
    }
  }, [isOpen, activeProfile]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const trimmedName = displayName.trim();
    if (!trimmedName || trimmedName.length < 1 || trimmedName.length > 50) {
      setError('Display name must be between 1 and 50 characters.');
      return;
    }

    const parsedHeight = parseFloat(heightCm);
    if (isNaN(parsedHeight) || parsedHeight < 100 || parsedHeight > 250) {
      setError('Height must be a valid number between 100 and 250 cm.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        display_name: trimmedName,
        height_cm: Math.round(parsedHeight * 10) / 10
      };

      const res = await profileService.updateMyPersonalDetails(payload);
      if (res?.success) {
        setSuccess('Personal details updated successfully!');
        const updated = {
          ...(activeProfile || {}),
          name: res.profile?.display_name || trimmedName,
          display_name: res.profile?.display_name || trimmedName,
          height_cm: res.profile?.height_cm || payload.height_cm,
          default_height_cm: res.profile?.height_cm || payload.height_cm
        };
        profileService.saveActiveProfile(updated);
        if (onProfileUpdated) {
          onProfileUpdated(updated);
        }
        setTimeout(() => {
          onClose();
        }, 1000);
      } else {
        setError(res?.error || 'Failed to update personal details. Please try again.');
      }
    } catch (err) {
      setError(err?.message || 'Network error occurred while saving.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(5, 8, 22, 0.82)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '16px'
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#0E1330',
          border: '1px solid #2D3561',
          borderRadius: '16px',
          padding: '32px',
          width: '100%',
          maxWidth: '460px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(0, 212, 170, 0.1)',
          color: '#ffffff',
          position: 'relative'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                backgroundColor: 'rgba(0, 212, 170, 0.15)',
                color: '#00D4AA',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '18px',
                fontWeight: 'bold'
              }}
            >
              👤
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '700', color: '#ffffff' }}>
                My Profile
              </h2>
              <p style={{ margin: 0, fontSize: '13px', color: '#a0aec0' }}>
                Edit Personal Details
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#a0aec0',
              fontSize: '20px',
              cursor: 'pointer',
              padding: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '6px'
            }}
            title="Close"
          >
            ✕
          </button>
        </div>

        {/* Read-Only Notice Banner */}
        <div
          style={{
            backgroundColor: 'rgba(45, 53, 97, 0.45)',
            border: '1px solid #2D3561',
            borderRadius: '10px',
            padding: '12px 14px',
            marginBottom: '22px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px'
          }}
        >
          <span style={{ fontSize: '16px', lineHeight: '1.2' }}>ℹ️</span>
          <p
            style={{
              margin: 0,
              fontSize: '12.5px',
              color: '#cbd5e0',
              lineHeight: '1.45'
            }}
          >
            Profile type, relationship, invitations, and profile access are managed by the account owner.
          </p>
        </div>

        {/* Alerts */}
        {error && (
          <div
            style={{
              backgroundColor: 'rgba(245, 101, 101, 0.15)',
              border: '1px solid #f56565',
              color: '#feb2b2',
              padding: '10px 14px',
              borderRadius: '8px',
              fontSize: '13px',
              marginBottom: '16px'
            }}
          >
            {error}
          </div>
        )}

        {success && (
          <div
            style={{
              backgroundColor: 'rgba(72, 187, 120, 0.15)',
              border: '1px solid #48bb78',
              color: '#9ae6b4',
              padding: '10px 14px',
              borderRadius: '8px',
              fontSize: '13px',
              marginBottom: '16px'
            }}
          >
            {success}
          </div>
        )}

        {/* Edit Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Display Name Field */}
          <div>
            <label
              htmlFor="member-display-name"
              style={{
                display: 'block',
                fontSize: '13px',
                fontWeight: '600',
                color: '#cbd5e0',
                marginBottom: '6px'
              }}
            >
              Display Name
            </label>
            <input
              id="member-display-name"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g. John Doe"
              maxLength={50}
              disabled={loading || fetching}
              style={{
                width: '100%',
                padding: '10px 14px',
                backgroundColor: '#1E2340',
                border: '1px solid #2D3561',
                borderRadius: '8px',
                color: '#ffffff',
                fontSize: '14px',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {/* Height Field */}
          <div>
            <label
              htmlFor="member-height-cm"
              style={{
                display: 'block',
                fontSize: '13px',
                fontWeight: '600',
                color: '#cbd5e0',
                marginBottom: '6px'
              }}
            >
              Height (cm)
            </label>
            <input
              id="member-height-cm"
              type="number"
              step="0.1"
              min="100"
              max="250"
              value={heightCm}
              onChange={(e) => setHeightCm(e.target.value)}
              placeholder="170"
              disabled={loading || fetching}
              style={{
                width: '100%',
                padding: '10px 14px',
                backgroundColor: '#1E2340',
                border: '1px solid #2D3561',
                borderRadius: '8px',
                color: '#ffffff',
                fontSize: '14px',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            />
            <span style={{ fontSize: '11.5px', color: '#718096', marginTop: '4px', display: 'block' }}>
              Used for body model scaling in future measurements (100 – 250 cm).
            </span>
          </div>

          {/* Action Buttons */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              gap: '12px',
              marginTop: '12px'
            }}
          >
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              style={{
                padding: '9px 18px',
                backgroundColor: 'transparent',
                border: '1px solid #2D3561',
                borderRadius: '8px',
                color: '#cbd5e0',
                fontWeight: '600',
                fontSize: '13px',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || fetching}
              style={{
                padding: '9px 22px',
                backgroundColor: '#00D4AA',
                border: 'none',
                borderRadius: '8px',
                color: '#0A0E27',
                fontWeight: '700',
                fontSize: '13.5px',
                cursor: (loading || fetching) ? 'not-allowed' : 'pointer',
                opacity: (loading || fetching) ? 0.7 : 1,
                boxShadow: '0 4px 12px rgba(0, 212, 170, 0.3)'
              }}
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
