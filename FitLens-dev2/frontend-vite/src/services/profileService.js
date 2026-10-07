import { authHeaders, profileAuthHeaders, saveProfileSessionToken, saveActiveProfileId, saveAccessMode, clearAllAuthSessions } from './authService';

const API = 'http://localhost:5000';
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

  clearUnlockedProfileId: () => {
    try {
      localStorage.removeItem('fitlens_unlocked_profile_id');
      localStorage.removeItem('fitlens_member_email');
    } catch (e) {
      console.error('Failed to clear unlocked profile id:', e);
    }
  }
};
