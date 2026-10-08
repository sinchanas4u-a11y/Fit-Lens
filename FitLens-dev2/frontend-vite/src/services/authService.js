export const getCandidateAuthBases = () => {
  const bases = [];
  if (typeof window !== 'undefined') {
    bases.push('');
    const host = window.location.hostname;
    if (host) {
      bases.push(`http://${host}:5000`);
    }
  }
  bases.push('http://127.0.0.1:5000');
  bases.push('http://localhost:5000');
  return [...new Set(bases)];
};

export const resilientFetchAuth = async (endpoint, options = {}) => {
  const bases = getCandidateAuthBases();
  let lastErr = null;
  for (const base of bases) {
    try {
      const url = `${base}${endpoint}`;
      return await fetch(url, options);
    } catch (err) {
      lastErr = err;
      continue;
    }
  }
  throw lastErr || new Error('Network error: Unable to connect to FitLens server.');
};

export const register = async (name, email, password) => {
  const res = await resilientFetchAuth('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password })
  });
  return res.json();
};

export const login = async (email, password) => {
  const res = await resilientFetchAuth('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  return res.json();
};

const API = '';

export const getCurrentUser = async () => {
  const token = getProfileSessionToken() || getAccountAuthToken();
  if (!token) return null;
  try {
    const res = await resilientFetchAuth('/api/auth/me', {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    if (!res.ok) {
      if (getProfileSessionToken()) {
        clearAllAuthSessions();
      } else {
        removeToken();
      }
      return null;
    }
    const data = await res.json();
    if (!data.success) {
      if (getProfileSessionToken()) {
        clearAllAuthSessions();
      } else {
        removeToken();
      }
      return null;
    }
    return data.user;
  } catch (e) {
    return null;
  }
};

// Account Auth Token (Owner account credentials)
export const getAccountAuthToken = () => localStorage.getItem('fitlens_account_auth_token') || localStorage.getItem('fitlens_token');
export const saveAccountAuthToken = (token) => {
  if (token) {
    localStorage.setItem('fitlens_account_auth_token', token);
    localStorage.setItem('fitlens_token', token);
  }
};
export const getToken = getAccountAuthToken;
export const saveToken = (token) => saveAccountAuthToken(token);
export const removeToken = () => {
  localStorage.removeItem('fitlens_token');
  localStorage.removeItem('fitlens_account_auth_token');
};

// Restricted Profile Session Token
export const getProfileSessionToken = () => localStorage.getItem('fitlens_profile_session_token');
export const saveProfileSessionToken = (token) => {
  if (token) {
    localStorage.setItem('fitlens_profile_session_token', token);
  } else {
    localStorage.removeItem('fitlens_profile_session_token');
  }
};

// Account User ID & Active Profile ID
export const getAccountUserId = () => localStorage.getItem('fitlens_account_user_id');
export const saveAccountUserId = (id) => {
  if (id) {
    localStorage.setItem('fitlens_account_user_id', String(id));
  } else {
    localStorage.removeItem('fitlens_account_user_id');
  }
};

export const getActiveProfileId = () => localStorage.getItem('fitlens_active_profile_id');
export const saveActiveProfileId = (id) => {
  if (id) {
    localStorage.setItem('fitlens_active_profile_id', String(id));
  } else {
    localStorage.removeItem('fitlens_active_profile_id');
  }
};

// Access Mode: 'owner_profile' | 'invited_profile'
export const getAccessMode = () => localStorage.getItem('fitlens_access_mode');
export const saveAccessMode = (mode) => {
  if (mode) {
    localStorage.setItem('fitlens_access_mode', String(mode));
  } else {
    localStorage.removeItem('fitlens_access_mode');
  }
};

export const isLoggedIn = () => !!getAccountAuthToken() || !!getProfileSessionToken();

// Auth Headers for Owner / Account Management
export const authHeaders = () => {
  const token = getAccountAuthToken() || getProfileSessionToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

// Profile-scoped Headers for Measurement & Analysis
export const profileAuthHeaders = () => {
  const token = getProfileSessionToken() || getAccountAuthToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const pid = getActiveProfileId();
  if (pid) {
    headers['X-Active-Profile-Id'] = String(pid);
  }
  return headers;
};

// Clear all authentication & profile session data
export const clearAllAuthSessions = () => {
  try {
    localStorage.removeItem('fitlens_token');
    localStorage.removeItem('fitlens_account_auth_token');
    localStorage.removeItem('fitlens_profile_session_token');
    localStorage.removeItem('fitlens_account_user_id');
    localStorage.removeItem('fitlens_active_profile_id');
    localStorage.removeItem('fitlens_access_mode');
    localStorage.removeItem('fitlens_active_profile');
    localStorage.removeItem('fitlens_unlocked_profile_id');
    localStorage.removeItem('fitlens_member_email');
    localStorage.removeItem('fitlens_user');
    sessionStorage.clear();
  } catch (err) {
    console.error('Error clearing sessions:', err);
  }
};

export const forgotPassword = async (email) => {
  const res = await fetch(`${API}/api/auth/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  return res.json();
};

export const resetPassword = async (token, newPassword, confirmPassword) => {
  const res = await fetch(`${API}/api/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      token,
      new_password: newPassword,
      confirm_password: confirmPassword || newPassword
    })
  });
  return res.json();
};

export const changePassword = async (currentPassword, newPassword, confirmPassword) => {
  const res = await fetch(`${API}/api/auth/change-password`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword || newPassword
    })
  });
  return res.json();
};

export const updateProfile = async (name) => {
  const res = await fetch(`${API}/api/auth/update-profile`, {
    method: 'PUT',
    headers: authHeaders(),
    body: JSON.stringify({ name })
  });
  return res.json();
};

export const deleteAccount = async (password) => {
  const res = await fetch(`${API}/api/auth/delete-account`, {
    method: 'DELETE',
    headers: authHeaders(),
    body: JSON.stringify({ password })
  });
  return res.json();
};

export const deleteMeasurement = async (analysisId) => {
  const res = await fetch(`${API}/api/measurements/delete/${analysisId}`, {
    method: 'DELETE',
    headers: profileAuthHeaders()
  });
  return res.json();
};
