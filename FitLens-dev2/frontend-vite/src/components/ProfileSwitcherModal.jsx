import React, { useState } from 'react';
import { profileService } from '../services/profileService';

export default function ProfileSwitcherModal({
  isOpen,
  onClose,
  profiles,
  activeProfile,
  onProfileSelected,
  onOpenSettings,
  slotUsage = { active_count: 1, max_slots: 4 }
}) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newRelationship, setNewRelationship] = useState('Spouse');
  const [newHeight, setNewHeight] = useState('170');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const isFull = (slotUsage.active_count || profiles.length) >= (slotUsage.max_slots || 4);
  const isCurrentOwner = Boolean(
    activeProfile?.is_owner ||
    activeProfile?.profile_type === 'owner'
  );

  const handleSelect = (profile) => {
    if (!isCurrentOwner) {
      setError('Only the account owner has permission to switch profiles.');
      return;
    }
    profileService.saveActiveProfile(profile);
    if (onProfileSelected) onProfileSelected(profile);
    onClose();
  };

  const handleCreateProfile = async (e) => {
    e.preventDefault();
    setError(null);

    if (!isCurrentOwner) {
      setError('Only the account owner has permission to create profiles.');
      return;
    }

    const trimmed = newName.trim();
    if (!trimmed || trimmed.length < 1 || trimmed.length > 50) {
      setError('Name must be between 1 and 50 characters.');
      return;
    }

    const h = parseFloat(newHeight);
    if (isNaN(h) || h < 100 || h > 250) {
      setError('Height must be between 100 and 250 cm.');
      return;
    }

    setLoading(true);
    try {
      const res = await profileService.createProfile({
        name: trimmed,
        relationship: newRelationship,
        default_height_cm: h,
        profile_type: newRelationship.toLowerCase() === 'child' ? 'child' : 'adult'
      });

      if (res.success && res.profile) {
        setNewName('');
        setShowAddForm(false);
        handleSelect(res.profile);
      } else {
        setError(res.error || 'Failed to create profile.');
      }
    } catch (err) {
      setError(err.message || 'Error creating profile.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={s.overlay} onClick={onClose}>
      <div style={s.modal} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={s.header}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '26px' }}>👥</span>
            <div>
              <h2 style={s.title}>Switch Profile</h2>
              <p style={s.sub}>Who is taking measurements today?</p>
            </div>
          </div>
          <button style={s.closeBtn} onClick={onClose}>✕</button>
        </div>

        {/* Member Profile Notice Banner */}
        {!isCurrentOwner && (
          <div style={{
            backgroundColor: 'rgba(255, 179, 0, 0.1)',
            border: '1px solid rgba(255, 179, 0, 0.35)',
            borderRadius: '10px',
            padding: '10px 14px',
            marginBottom: '16px',
            fontSize: '12px',
            color: '#ffe082',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span>🔒</span>
            <span>
              <strong>Member Mode ({activeProfile?.name}):</strong> You can only access your own profile. Only the owner can manage or add profiles.
            </span>
          </div>
        )}

        {/* Slot Capacity Pill */}
        <div style={s.capacityBar}>
          <span style={s.capacityLabel}>
            Account Profile Slots: <strong style={{ color: isFull ? '#fc8181' : '#00D4AA' }}>
              {slotUsage.active_count || profiles.length} / {slotUsage.max_slots || 4} Active
            </strong>
          </span>
          <span style={{ fontSize: '12px', color: '#a0aec0' }}>
            {isFull ? '⚠️ Slot limit reached' : `${(slotUsage.max_slots || 4) - (slotUsage.active_count || profiles.length)} slots available`}
          </span>
        </div>

        {error && <div style={s.errorBox}>⚠️ {error}</div>}

        {/* Profiles List */}
        {!showAddForm ? (
          <>
            <div style={s.grid}>
              {profiles.map(p => {
                const isActive = activeProfile?.id === p.id;
                const initial = (p.name || 'U').charAt(0).toUpperCase();
                const canSelect = isCurrentOwner && !isActive;
                return (
                  <div
                    key={p.id}
                    onClick={() => canSelect && handleSelect(p)}
                    style={{
                      ...s.card,
                      cursor: isActive ? 'default' : canSelect ? 'pointer' : 'not-allowed',
                      opacity: canSelect || isActive ? 1 : 0.6,
                      borderColor: isActive ? '#00D4AA' : '#2D3561',
                      background: isActive ? 'linear-gradient(135deg, rgba(0,212,170,0.12), #1E2340)' : '#161B36',
                      boxShadow: isActive ? '0 0 16px rgba(0,212,170,0.25)' : 'none'
                    }}
                  >
                    <div style={{ ...s.avatar, background: isActive ? 'linear-gradient(135deg, #00D4AA, #0080FF)' : '#2D3561' }}>
                      {initial}
                    </div>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <h4 style={s.cardName}>{p.name}</h4>
                        <span style={{
                          ...s.badge,
                          background: p.is_owner ? 'rgba(0,212,170,0.2)' : 'rgba(160,174,192,0.15)',
                          color: p.is_owner ? '#00D4AA' : '#a0aec0'
                        }}>
                          {p.is_owner ? 'Owner' : (p.relationship || 'Member')}
                        </span>
                      </div>
                      <p style={s.cardSub}>
                        Default Height: <strong style={{ color: '#ffffff' }}>{p.default_height_cm || 170} cm</strong>
                      </p>
                      {p.latest_measurement_date && (
                        <p style={{ ...s.cardSub, fontSize: '11px', color: '#718096' }}>
                          Last scan: {p.latest_measurement_date}
                        </p>
                      )}
                    </div>

                    {isActive ? (
                      <span style={s.activeBadge}>✓ Active</span>
                    ) : isCurrentOwner ? (
                      <button style={s.selectBtn} onClick={(e) => { e.stopPropagation(); handleSelect(p); }}>
                        Select
                      </button>
                    ) : (
                      <span style={{ ...s.badge, background: '#101428', border: '1px solid #2D3561', color: p.is_owner ? '#00D4AA' : '#718096' }}>
                        {p.is_owner ? '👑 Owner' : '🔒 Member'}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Actions */}
            <div style={s.footerActions}>
              {isCurrentOwner && !isFull && (
                <button style={s.addBtn} onClick={() => setShowAddForm(true)}>
                  ➕ Add Family Profile
                </button>
              )}
              {onOpenSettings && (
                <button
                  style={s.manageBtn}
                  onClick={() => {
                    onClose();
                    onOpenSettings('profiles');
                  }}
                >
                  ⚙️ Manage Profiles in Settings
                </button>
              )}
            </div>
          </>
        ) : (
          /* Add Profile Form */
          <form onSubmit={handleCreateProfile} style={s.addForm}>
            <h3 style={{ margin: '0 0 16px', color: '#00D4AA', fontSize: '16px' }}>
              ➕ Create New Profile
            </h3>

            <div style={s.field}>
              <label style={s.label}>FULL NAME</label>
              <input
                type="text"
                placeholder="e.g. Sarah, Alex, or Child"
                value={newName}
                onChange={e => setNewName(e.target.value)}
                style={s.input}
                required
              />
            </div>

            <div style={s.field}>
              <label style={s.label}>RELATIONSHIP</label>
              <select
                value={newRelationship}
                onChange={e => setNewRelationship(e.target.value)}
                style={s.input}
              >
                <option value="Spouse">Spouse</option>
                <option value="Child">Child</option>
                <option value="Parent">Parent</option>
                <option value="Sibling">Sibling</option>
                <option value="Friend">Friend</option>
                <option value="Family">Family Member</option>
              </select>
            </div>

            <div style={s.field}>
              <label style={s.label}>DEFAULT HEIGHT (CM)</label>
              <input
                type="number"
                placeholder="170"
                min="100"
                max="250"
                step="0.5"
                value={newHeight}
                onChange={e => setNewHeight(e.target.value)}
                style={s.input}
                required
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
              <button
                type="submit"
                disabled={loading}
                style={{
                  ...s.addBtn,
                  flex: 1,
                  background: 'linear-gradient(135deg, #00D4AA, #0080FF)',
                  color: '#ffffff'
                }}
              >
                {loading ? 'Creating...' : 'Create & Select Profile'}
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                style={{ ...s.manageBtn, flex: 1 }}
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

const s = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(5, 8, 22, 0.85)',
    backdropFilter: 'blur(8px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
    padding: '20px'
  },
  modal: {
    backgroundColor: '#1E2340',
    border: '1px solid #2D3561',
    borderRadius: '20px',
    maxWidth: '560px',
    width: '100%',
    padding: '28px',
    color: '#ffffff',
    boxShadow: '0 24px 48px rgba(0, 0, 0, 0.5)',
    maxHeight: '90vh',
    overflowY: 'auto'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px'
  },
  title: {
    margin: 0,
    fontSize: '20px',
    fontWeight: '800',
    color: '#ffffff'
  },
  sub: {
    margin: '4px 0 0',
    fontSize: '13px',
    color: '#a0aec0'
  },
  closeBtn: {
    background: '#0a0e27',
    border: '1px solid #2D3561',
    color: '#a0aec0',
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    fontSize: '16px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  capacityBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#0a0e27',
    padding: '10px 16px',
    borderRadius: '10px',
    marginBottom: '20px',
    border: '1px solid #2D3561'
  },
  capacityLabel: {
    fontSize: '13px',
    color: '#cbd5e0'
  },
  grid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    marginBottom: '24px'
  },
  card: {
    display: 'flex',
    alignItems: 'center',
    gap: '14px',
    padding: '16px 20px',
    borderRadius: '14px',
    border: '1px solid #2D3561',
    cursor: 'pointer',
    transition: 'all 0.2s ease'
  },
  avatar: {
    width: '46px',
    height: '46px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: '800',
    fontSize: '18px',
    color: '#ffffff',
    flexShrink: 0
  },
  cardName: {
    margin: 0,
    fontSize: '16px',
    fontWeight: '700',
    color: '#ffffff'
  },
  badge: {
    fontSize: '11px',
    fontWeight: '700',
    padding: '3px 8px',
    borderRadius: '999px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  },
  cardSub: {
    margin: 0,
    fontSize: '13px',
    color: '#a0aec0'
  },
  activeBadge: {
    backgroundColor: 'rgba(0, 212, 170, 0.15)',
    color: '#00D4AA',
    border: '1px solid #00D4AA',
    padding: '6px 12px',
    borderRadius: '8px',
    fontWeight: '700',
    fontSize: '12px'
  },
  selectBtn: {
    backgroundColor: '#2D3561',
    color: '#ffffff',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '8px',
    fontWeight: '600',
    fontSize: '13px',
    cursor: 'pointer'
  },
  footerActions: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap'
  },
  addBtn: {
    flex: 1,
    padding: '12px 18px',
    background: '#00D4AA',
    color: '#0a0e27',
    border: 'none',
    borderRadius: '10px',
    fontWeight: '700',
    fontSize: '14px',
    cursor: 'pointer',
    whiteSpace: 'nowrap'
  },
  manageBtn: {
    flex: 1,
    padding: '12px 18px',
    background: 'transparent',
    color: '#00D4AA',
    border: '1px solid #2D3561',
    borderRadius: '10px',
    fontWeight: '600',
    fontSize: '14px',
    cursor: 'pointer',
    whiteSpace: 'nowrap'
  },
  errorBox: {
    background: 'rgba(252, 129, 129, 0.15)',
    border: '1px solid #fc8181',
    color: '#fc8181',
    padding: '10px 14px',
    borderRadius: '8px',
    marginBottom: '16px',
    fontSize: '13px'
  },
  addForm: {
    backgroundColor: '#161B36',
    border: '1px solid #2D3561',
    borderRadius: '14px',
    padding: '20px'
  },
  field: {
    marginBottom: '14px',
    textAlign: 'left'
  },
  label: {
    display: 'block',
    fontSize: '11px',
    fontWeight: '700',
    color: '#a0aec0',
    marginBottom: '6px',
    letterSpacing: '0.5px'
  },
  input: {
    width: '100%',
    padding: '12px 14px',
    backgroundColor: '#0a0e27',
    border: '1px solid #2D3561',
    borderRadius: '8px',
    color: '#ffffff',
    fontSize: '14px',
    outline: 'none',
    boxSizing: 'border-box'
  }
};
