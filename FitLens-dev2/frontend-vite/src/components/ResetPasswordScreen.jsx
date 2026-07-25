import React, { useState, useEffect } from 'react';

const ResetPasswordScreen = () => {
  const token = new URLSearchParams(window.location.search).get('token');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    if (!token) {
      window.location.href = '/';
    }
  }, [token]);

  const handleReset = async (e) => {
    if (e) e.preventDefault();
    setError('');
    if (!newPassword || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          new_password: newPassword,
          confirm_password: confirmPassword
        })
      });
      const data = await res.json();
      if (data.success) {
        setSuccess(true);
        setTimeout(() => {
          window.location.href = '/?reset=success';
        }, 3000);
      } else {
        setError(data.error || 'Reset failed. Please try again.');
      }
    } catch {
      setError('Connection error. Please try again.');
    }
    setLoading(false);
  };

  if (success) {
    return (
      <div style={s.page}>
        <div style={s.card}>
          <div style={{ fontSize: 56, marginBottom: 16 }}>✅</div>
          <h2 style={{ color: '#00d4aa' }}>Password Reset!</h2>
          <p style={{ color: '#a0aec0' }}>
            Your password has been updated successfully.<br />
            Redirecting to login in 3 seconds...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={{ fontSize: 48, marginBottom: 8 }}>🔐</div>
        <h2 style={{ color: '#00d4aa', marginBottom: 8 }}>Set New Password</h2>
        <p style={{ color: '#a0aec0', marginBottom: 24, fontSize: 14 }}>
          Enter and confirm your new password below.
        </p>

        <form onSubmit={handleReset}>
          <div style={s.inputWrap}>
            <input
              type={showNew ? 'text' : 'password'}
              placeholder="New password (min 8 characters)"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              style={s.input}
            />
            <span onClick={() => setShowNew(!showNew)} style={s.eye}>
              {showNew ? '🙈' : '👁️'}
            </span>
          </div>

          <div style={s.inputWrap}>
            <input
              type={showConfirm ? 'text' : 'password'}
              placeholder="Confirm new password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              style={s.input}
            />
            <span onClick={() => setShowConfirm(!showConfirm)} style={s.eye}>
              {showConfirm ? '🙈' : '👁️'}
            </span>
          </div>

          {error && <div style={s.error}>⚠️ {error}</div>}

          <button type="submit" disabled={loading} style={s.btn}>
            {loading ? 'Resetting...' : '🔒 Reset Password'}
          </button>
          <button type="button" onClick={() => window.location.href = '/'} style={s.cancel}>
            Back to Login
          </button>
        </form>
      </div>
    </div>
  );
};

const s = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg,#0a0e27,#1a1f3a)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: '20px', fontFamily: 'Inter, system-ui, sans-serif'
  },
  card: {
    background: '#1e2340', border: '1px solid #2d3561',
    borderRadius: 16, padding: 40, width: '100%',
    maxWidth: 420, textAlign: 'center', color: '#fff'
  },
  inputWrap: { position: 'relative', marginBottom: 16 },
  input: {
    width: '100%', padding: '13px 44px 13px 16px',
    background: '#0a0e27', border: '1px solid #2d3561',
    borderRadius: 8, color: '#fff', fontSize: 15,
    outline: 'none', boxSizing: 'border-box'
  },
  eye: {
    position: 'absolute', right: 12, top: '50%',
    transform: 'translateY(-50%)', cursor: 'pointer', fontSize: 18
  },
  error: {
    background: 'rgba(252,129,129,0.1)', border: '1px solid #fc8181',
    color: '#fc8181', padding: '10px 16px',
    borderRadius: 8, marginBottom: 16, fontSize: 14
  },
  btn: {
    width: '100%', padding: 14,
    background: 'linear-gradient(135deg,#00d4aa,#0080ff)',
    color: '#fff', border: 'none', borderRadius: 10,
    fontSize: 16, fontWeight: 700, cursor: 'pointer', marginBottom: 12
  },
  cancel: {
    width: '100%', padding: 12, background: 'transparent',
    color: '#a0aec0', border: '1px solid #2d3561',
    borderRadius: 10, fontSize: 14, cursor: 'pointer'
  }
};

export default ResetPasswordScreen;
