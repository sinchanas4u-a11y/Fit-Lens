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
    const data = await res.json();
    return data.success ? data.user : null;
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
