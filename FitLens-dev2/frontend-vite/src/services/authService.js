const API = 'http://localhost:5000';

export const register = async (name, email, password) => {
  const res = await fetch(`${API}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password })
  });
  return res.json();
};

export const login = async (email, password) => {
  const res = await fetch(`${API}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  return res.json();
};

export const getCurrentUser = async () => {
  const token = getToken();
  if (!token) return null;
  try {
    const res = await fetch(`${API}/api/auth/me`, {
      headers: authHeaders()
    });
    if (!res.ok) {
      removeToken();
      return null;
    }
    const data = await res.json();
    if (!data.success) {
      removeToken();
      return null;
    }
    return data.user;
  } catch (e) {
    return null;
  }
};

export const getToken = () => localStorage.getItem('fitlens_token');
export const saveToken = (token) => localStorage.setItem('fitlens_token', token);
export const removeToken = () => localStorage.removeItem('fitlens_token');
export const isLoggedIn = () => !!getToken();

export const authHeaders = () => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${getToken()}`
});

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
    headers: authHeaders()
  });
  return res.json();
};

