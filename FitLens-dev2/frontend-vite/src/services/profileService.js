import { authHeaders, profileAuthHeaders, saveProfileSessionToken, saveActiveProfileId, saveAccessMode, clearAllAuthSessions } from './authService';

export const getCandidateApiBases = () => {
  const bases = [];
  if (typeof window !== 'undefined') {
    // 1. Same-origin relative path (leverages Vite dev proxy)
    bases.push('');
    // 2. Direct backend host on port 5000 (cross-origin direct to Flask)
    const host = window.location.hostname;
    if (host) {
      bases.push(`http://${host}:5000`);
    }
  }
  bases.push('http://127.0.0.1:5000');
  bases.push('http://localhost:5000');
  return [...new Set(bases)];
};

export const resilientFetch = async (endpoint, options = {}) => {
  const bases = getCandidateApiBases();
  let lastErr = null;
  for (const base of bases) {
    try {
      const url = `${base}${endpoint}`;
      const res = await fetch(url, options);
      return res;
    } catch (err) {
      lastErr = err;
      // Network error occurred (e.g. Failed to fetch), try next candidate base
      continue;
    }
  }
  throw lastErr || new Error('Network error: Unable to connect to FitLens server.');
};

const API = '';
const ACTIVE_PROFILE_KEY = 'fitlens_active_profile';

const getProfileHeaders = () => {
  const headers = authHeaders();
  try {
    const saved = localStorage.getItem(ACTIVE_PROFILE_KEY);
    if (saved) {
      const active = JSON.parse(saved);
      if (active?.id) {
        headers['X-Active-Profile-Id'] = String(active.id);
      }
    }
  } catch (e) {
    // fallback
  }
  return headers;
};

export const profileService = {
  // Fetch all profiles for the current user's account (Owner management)
  listProfiles: async () => {
    try {
      const res = await fetch(`${API}/api/profiles`, {
        headers: getProfileHeaders()
      });
      return await res.json();
    } catch (err) {
      console.error('Failed to list profiles:', err);
      return { success: false, error: err.message, profiles: [] };
    }
  },

  // Fetch safe available profiles metadata for profile selection screen (all locked initially)
  getAvailableProfiles: async () => {
    try {
      const res = await fetch(`${API}/api/profiles/available`, {
        headers: authHeaders()
      });
      return await res.json();
    } catch (err) {
      console.error('Failed to fetch available profiles:', err);
      return { success: false, error: err.message, profiles: [] };
    }
  },

  // Unlock invited non-owner profile using invited email
  unlockInvitedProfile: async (invitedEmail) => {
    try {
      const res = await fetch(`${API}/api/profiles/unlock-invited`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ invited_email: (invitedEmail || '').trim().toLowerCase() })
      });
      const data = await res.json();
      if (data.success && data.profile_session_token) {
        saveProfileSessionToken(data.profile_session_token);
        saveAccessMode('invited_profile');
        if (data.profile?.profile_id || data.profile?.id) {
          saveActiveProfileId(data.profile.profile_id || data.profile.id);
        }
      }
      return data;
    } catch (err) {
      console.error('Failed to unlock invited profile:', err);
      return { success: false, error: err.message };
    }
  },

  // Unlock owner profile using owner authentication
  unlockOwnerProfile: async (password = null) => {
    try {
      const body = {};
      if (password) body.password = password;
      const res = await fetch(`${API}/api/profiles/unlock-owner`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (data.success && data.profile_session_token) {
        saveProfileSessionToken(data.profile_session_token);
        saveAccessMode('owner_profile');
        if (data.profile?.profile_id || data.profile?.id) {
          saveActiveProfileId(data.profile.profile_id || data.profile.id);
        }
      }
      return data;
    } catch (err) {
      console.error('Failed to unlock owner profile:', err);
      return { success: false, error: err.message };
    }
  },

  // Create a new managed profile (child, spouse, dependent, etc.)
  createProfile: async (data) => {
    try {
      const res = await fetch(`${API}/api/profiles`, {
        method: 'POST',
        headers: getProfileHeaders(),
        body: JSON.stringify(data)
      });
      return await res.json();
    } catch (err) {
      console.error('Failed to create profile:', err);
      return { success: false, error: err.message };
    }
  },

  // Update profile name, height, or relationship
  updateProfile: async (profileId, data) => {
    try {
      const res = await fetch(`${API}/api/profiles/${profileId}`, {
        method: 'PATCH',
        headers: getProfileHeaders(),
        body: JSON.stringify(data)
      });
      return await res.json();
    } catch (err) {
      console.error('Failed to update profile:', err);
      return { success: false, error: err.message };
    }
  },

  // Archive a profile to free up 1 of the 4 slots
  archiveProfile: async (profileId) => {
    try {
      const res = await fetch(`${API}/api/profiles/${profileId}/archive`, {
        method: 'POST',
        headers: getProfileHeaders()
      });
      return await res.json();
    } catch (err) {
      console.error('Failed to archive profile:', err);
      return { success: false, error: err.message };
    }
  },

  // Delete a profile
  deleteProfile: async (profileId) => {
    try {
      const res = await fetch(`${API}/api/profiles/${profileId}`, {
        method: 'DELETE',
        headers: getProfileHeaders()
      });
      return await res.json();
    } catch (err) {
      console.error('Failed to delete profile:', err);
      return { success: false, error: err.message };
    }
  },

  // Send email invitation to an adult family member
  createInvite: async (data) => {
    try {
      const payload = {
        ...data,
        client_base_url: typeof window !== 'undefined' ? window.location.origin : ''
      };
      const res = await fetch(`${API}/api/profile-invites`, {
        method: 'POST',
        headers: getProfileHeaders(),
        body: JSON.stringify(payload)
      });
      const contentType = res.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        const text = await res.text();
        return { success: false, error: `Server error (${res.status}): unexpected response format` };
      }
      const json = await res.json();
      if (!res.ok) {
        return { success: false, error: json.error || `Failed to send invitation (${res.status})` };
      }
      return json;
    } catch (err) {
      console.error('Failed to invite profile:', err);
      return { success: false, error: err.message };
    }
  },

  // List all invitations for account
  listInvites: async () => {
    try {
      const res = await fetch(`${API}/api/profile-invites`, {
        headers: getProfileHeaders()
      });
      return await res.json();
    } catch (err) {
      console.error('Failed to list invites:', err);
      return { success: false, error: err.message, invites: [] };
    }
  },

  // Revoke an active invitation
  revokeInvite: async (inviteId) => {
    try {
      const res = await fetch(`${API}/api/profile-invites/${inviteId}`, {
        method: 'DELETE',
        headers: getProfileHeaders()
      });
      return await res.json();
    } catch (err) {
      console.error('Failed to revoke invite:', err);
      return { success: false, error: err.message };
    }
  },

  // Claim an invitation code or token to join an account
  claimInvite: async (claimData) => {
    try {
      const res = await fetch(`${API}/api/profile-invites/claim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(claimData)
      });
      const contentType = res.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        return { success: false, error: `Server error (${res.status}): unexpected response format` };
      }
      const json = await res.json();
      if (!res.ok) {
        return { success: false, error: json.error || `Failed to claim invitation (${res.status})` };
      }
      return json;
    } catch (err) {
      console.error('Failed to claim invite:', err);
      return { success: false, error: err.message };
    }
  },

  // Get active profile from localStorage
  getActiveProfile: () => {
    try {
      const saved = localStorage.getItem(ACTIVE_PROFILE_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  },

  // Save active profile to localStorage
  saveActiveProfile: (profile) => {
    try {
      if (profile) {
        localStorage.setItem(ACTIVE_PROFILE_KEY, JSON.stringify(profile));
        saveActiveProfileId(profile.id || profile.profile_id);
      } else {
        localStorage.removeItem(ACTIVE_PROFILE_KEY);
        saveActiveProfileId(null);
      }
    } catch (e) {
      console.error('Failed to save active profile:', e);
    }
  },

  // Non-owner member limited self-service editing: update display_name and height_cm only
  updateMyPersonalDetails: async (details) => {
    try {
      const res = await resilientFetch('/api/profiles/me/personal-details', {
        method: 'PATCH',
        headers: profileAuthHeaders(),
        body: JSON.stringify(details)
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        return {
          success: false,
          error: data?.error || 'Failed to update personal details.'
        };
      }
      return data || { success: true };
    } catch (err) {
      console.error('Failed to update personal details:', err);
      return { success: false, error: err.message || 'Network error.' };
    }
  },

  // Get own safe personal profile details for member session
  getMyPersonalDetails: async () => {
    try {
      const res = await resilientFetch('/api/profiles/me/personal-details', {
        headers: profileAuthHeaders()
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        return {
          success: false,
          error: data?.error || 'Failed to fetch personal details.'
        };
      }
      return data || { success: true };
    } catch (err) {
      console.error('Failed to fetch personal details:', err);
      return { success: false, error: err.message || 'Network error.' };
    }
  },

  // Backwards compatible unlock profile method
  unlockProfile: async (data) => {
    try {
      const res = await fetch(`${API}/api/profiles/unlock`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data)
      });
      const json = await res.json();
      if (json.success && json.profile_session_token) {
        saveProfileSessionToken(json.profile_session_token);
        saveAccessMode(data?.is_owner_unlock ? 'owner_profile' : 'invited_profile');
        if (json.unlocked_profile_id) {
          saveActiveProfileId(json.unlocked_profile_id);
        }
      }
      return json;
    } catch (err) {
      console.error('Failed to unlock profile:', err);
      return { success: false, error: err.message };
    }
  },

  getUnlockedProfileId: () => {
    try {
      return localStorage.getItem('fitlens_unlocked_profile_id') || null;
    } catch {
      return null;
    }
  },

  saveUnlockedProfileId: (id) => {
    try {
      if (id) {
        localStorage.setItem('fitlens_unlocked_profile_id', String(id));
      } else {
        localStorage.removeItem('fitlens_unlocked_profile_id');
      }
    } catch (e) {
      console.error('Failed to save unlocked profile id:', e);
    }
  },

  setUnlockedProfileId: (id) => {
    profileService.saveUnlockedProfileId(id);
  },

  clearUnlockedProfileId: () => {
    try {
      localStorage.removeItem('fitlens_unlocked_profile_id');
      localStorage.removeItem('fitlens_member_email');
    } catch (e) {
      console.error('Failed to clear unlocked profile id:', e);
    }
  },

  // Non-owner direct invitation token validation (no owner credentials required)
  validateInviteToken: async (token) => {
    try {
      const cleanToken = (token || '').trim();
      const res = await resilientFetch('/api/invite/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: cleanToken, invite_token: cleanToken })
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        return {
          success: false,
          error: data?.error || data?.message || 'This invitation is invalid, has expired, or was already accepted.'
        };
      }
      return data || { success: true };
    } catch (err) {
      console.error('Failed to validate invitation token:', err);
      return {
        success: false,
        error: err.message || 'Unable to connect to FitLens invitation service.'
      };
    }
  },

  // Non-owner owner approval OTP request (dispatches 6-digit code to owner's registered email only)
  requestOwnerOtp: async (inviteToken, ownerEmail) => {
    try {
      const cleanToken = (inviteToken || '').trim();
      const cleanEmail = (ownerEmail || '').trim().toLowerCase();
      const res = await resilientFetch('/api/invite/request-owner-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          invite_token: cleanToken,
          token: cleanToken,
          owner_email: cleanEmail
        })
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        return {
          success: false,
          error: data?.error || data?.message || 'The entered email does not match the account owner email address.'
        };
      }
      return data || { success: true };
    } catch (err) {
      console.error('Failed to request owner OTP:', err);
      return { success: false, error: err.message || 'Unable to connect to server.' };
    }
  },

  // Non-owner owner approval OTP verification & profile unlock
  verifyOwnerOtp: async (inviteToken, ownerEmail, otp, deviceLabel) => {
    try {
      const cleanToken = (inviteToken || '').trim();
      const cleanEmail = (ownerEmail || '').trim().toLowerCase();
      const cleanOtp = (otp || '').trim();
      const res = await resilientFetch('/api/invite/verify-owner-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          invite_token: cleanToken,
          token: cleanToken,
          owner_email: cleanEmail,
          otp: cleanOtp,
          device_label: deviceLabel || (typeof navigator !== 'undefined' ? navigator.userAgent : 'Mobile Browser')
        })
      });
      const json = await res.json().catch(() => null);
      if (!res.ok) {
        return {
          success: false,
          error: json?.error || json?.message || 'Incorrect verification code. Please check with the account owner.'
        };
      }
      if (json && json.success && json.profile_session_token) {
        saveProfileSessionToken(json.profile_session_token);
        saveAccessMode('invited_profile');
        if (json.profile?.profile_id || json.profile?.id) {
          saveActiveProfileId(json.profile.profile_id || json.profile.id);
          profileService.saveActiveProfile(json.profile);
        }
      }
      return json || { success: true };
    } catch (err) {
      console.error('Failed to verify owner OTP:', err);
      return { success: false, error: err.message || 'Unable to verify code.' };
    }
  },

  // Backwards compatible aliases
  requestInviteOtp: async (token, email) => {
    return profileService.requestOwnerOtp(token, email);
  },

  verifyInviteOtp: async (token, email, otp, deviceLabel) => {
    return profileService.verifyOwnerOtp(token, email, otp, deviceLabel);
  },

  // Owner in-app notifications
  getNotifications: async () => {
    try {
      const res = await fetch(`${API}/api/notifications`, {
        headers: authHeaders()
      });
      return await res.json();
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
      return { success: false, error: err.message, notifications: [] };
    }
  },

  // Mark notification read
  markNotificationRead: async (notificationId) => {
    try {
      const res = await fetch(`${API}/api/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: authHeaders()
      });
      return await res.json();
    } catch (err) {
      console.error('Failed to mark notification read:', err);
      return { success: false, error: err.message };
    }
  }
};
