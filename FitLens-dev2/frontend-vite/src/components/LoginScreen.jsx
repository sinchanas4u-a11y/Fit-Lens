import React, { useState } from 'react';
import { login, register, saveToken, forgotPassword } from '../services/authService';

export default function LoginScreen({ onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Forgot password state
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotSent, setForgotSent] = useState(false);
  const [forgotLoading, setForgotLoading] = useState(false);
  const [resetLink, setResetLink] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      let res;
      if (isRegister) {
        if (!name.trim()) {
          setError('Name is required');
          setLoading(false);
          return;
        }
        res = await register(name, email, password);
      } else {
        res = await login(email, password);
      }

      if (res.success && res.token) {
        saveToken(res.token);
        if (res.user) {
          localStorage.setItem('fitlens_user', JSON.stringify(res.user));
        }
        onLoginSuccess(res.user);
      } else {
        setError(res.error || 'Authentication failed');
      }
    } catch (err) {
      setError('Connection error. Please check backend server.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!forgotEmail.trim()) return;
    setForgotLoading(true);
    try {
      const res = await forgotPassword(forgotEmail.trim());
      if (res.success) {
        setForgotSent(true);
        if (res.reset_link) {
          setResetLink(res.reset_link);
        }
      } else {
        setError(res.error || 'Failed to send reset link');
      }
    } catch (err) {
      setError('Error connecting to reset service');
    } finally {
      setForgotLoading(false);
    }
  };

  const resetSuccess = new URLSearchParams(window.location.search).get('reset') === 'success';

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #0a0e27 0%, #1a1f3c 100%)',
      fontFamily: 'Inter, system-ui, sans-serif',
      color: '#ffffff',
      padding: '20px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '420px',
        backgroundColor: '#1E2340',
        borderRadius: '20px',
        border: '1px solid #2D3561',
        padding: '36px 30px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
        backdropFilter: 'blur(10px)'
      }}>
        {/* Header Branding */}
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <img
            src="/logo.png"
            alt="FitLens Logo"
            style={{ width: '70px', height: '70px', borderRadius: '16px', marginBottom: '12px' }}
            onError={(e) => { e.target.style.display = 'none'; }}
          />
          <h1 style={{ fontSize: '28px', fontWeight: '800', margin: '0 0 6px 0', color: '#ffffff' }}>
            Fit<span style={{ color: '#00D4AA' }}>Lens</span>
          </h1>
          <p style={{ color: '#a0aec0', fontSize: '14px', margin: 0 }}>
            {isRegister ? 'Create your account to save body scans' : 'Sign in to access your measurement profile'}
          </p>
        </div>

        {resetSuccess && (
          <div style={{
            backgroundColor: 'rgba(0, 212, 170, 0.15)',
            border: '1px solid #00D4AA',
            color: '#00D4AA',
            borderRadius: '10px',
            padding: '12px 16px',
            fontSize: '14px',
            marginBottom: '20px',
            textAlign: 'center'
          }}>
            ✅ Password reset successfully! Please log in with your new password.
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
            marginBottom: '20px',
            textAlign: 'center'
          }}>
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {isRegister && (
            <div>
              <label style={{ display: 'block', fontSize: '13px', color: '#a0aec0', marginBottom: '6px' }}>
                Full Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
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
          )}

          <div>
            <label style={{ display: 'block', fontSize: '13px', color: '#a0aec0', marginBottom: '6px' }}>
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="john@example.com"
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '13px', color: '#a0aec0' }}>
                Password
              </label>
              {!isRegister && (
                <button
                  type="button"
                  onClick={() => { setForgotEmail(email); setShowForgot(true); setForgotSent(false); }}
                  style={{ color: '#00D4AA', background: 'none', border: 'none', cursor: 'pointer', fontSize: '12px' }}
                >
                  Forgot Password?
                </button>
              )}
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
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
            disabled={loading}
            style={{
              marginTop: '10px',
              padding: '14px',
              backgroundColor: '#00D4AA',
              border: 'none',
              borderRadius: '12px',
              color: '#0a0e27',
              fontSize: '16px',
              fontWeight: '700',
              cursor: loading ? 'wait' : 'pointer',
              boxShadow: '0 4px 15px rgba(0, 212, 170, 0.3)',
              transition: 'all 0.2s'
            }}
          >
            {loading ? 'Processing...' : (isRegister ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <button
            onClick={() => {
              setIsRegister(!isRegister);
              setError(null);
            }}
            style={{
              background: 'none',
              border: 'none',
              color: '#00D4AA',
              fontSize: '14px',
              cursor: 'pointer',
              textDecoration: 'underline'
            }}
          >
            {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register"}
          </button>
        </div>
      </div>

      {/* Forgot Password Modal */}
      {showForgot && (
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
          zIndex: 1000,
          backdropFilter: 'blur(6px)'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '380px',
            backgroundColor: '#1E2340',
            border: '1px solid #2D3561',
            borderRadius: '20px',
            padding: '28px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.5)'
          }}>
            {!forgotSent ? (
              <>
                <h3 style={{ margin: '0 0 10px 0', fontSize: '20px', color: '#ffffff' }}>Reset Password</h3>
                <p style={{ color: '#a0aec0', fontSize: '13px', marginBottom: '20px', lineHeight: '1.4' }}>
                  Enter your email address and we'll send a password reset link valid for 15 minutes.
                </p>
                <form onSubmit={handleForgotPassword} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <input
                    type="email"
                    placeholder="Your email address"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    required
                    style={{
                      width: '100%',
                      padding: '12px 14px',
                      backgroundColor: '#0a0e27',
                      border: '1px solid #2D3561',
                      borderRadius: '10px',
                      color: '#ffffff',
                      fontSize: '14px',
                      outline: 'none',
                      boxSizing: 'border-box'
                    }}
                  />
                  <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
                    <button
                      type="button"
                      onClick={() => setShowForgot(false)}
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
                      disabled={forgotLoading}
                      style={{
                        flex: 1,
                        padding: '10px',
                        backgroundColor: '#00D4AA',
                        border: 'none',
                        borderRadius: '8px',
                        color: '#0a0e27',
                        fontWeight: '700',
                        cursor: forgotLoading ? 'wait' : 'pointer'
                      }}
                    >
                      {forgotLoading ? 'Sending...' : 'Send Link'}
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '40px', marginBottom: '12px' }}>✉️</div>
                <h3 style={{ color: '#ffffff', margin: '0 0 8px 0' }}>Request Processed</h3>
                <p style={{ color: '#a0aec0', fontSize: '14px', marginBottom: '20px', lineHeight: '1.5' }}>
                  If an account exists for this email address, we've sent a password reset link. Please check your inbox.
                </p>

                <button
                  onClick={() => { setShowForgot(false); setForgotSent(false); setResetLink(''); }}
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
                  Close
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

