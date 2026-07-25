import React, { useState, useEffect } from 'react';
import { updateProfile, changePassword, deleteAccount, deleteMeasurement, authHeaders } from '../services/authService';

export default function SettingsScreen({ user, onUserUpdated, onLogout, onClose }) {
  const [activeTab, setActiveTab] = useState('profile');
  const [msg, setMsg] = useState(null);
  const [error, setError] = useState(null);

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
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab]);

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

        {/* Tab 2: Security */}
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
    </div>
  );
}
