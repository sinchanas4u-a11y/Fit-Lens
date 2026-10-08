import React, { useState, useEffect } from 'react';
import { profileService } from '../services/profileService';
import logo from '../assets/logo.png';

export default function InviteClaimScreen({ token, onClaimSuccess, onCancel }) {
  const isInitialManual = !token || token === 'manual';
  const [currentToken, setCurrentToken] = useState(isInitialManual ? '' : token);
  const [validating, setValidating] = useState(!isInitialManual);
  const [validationError, setValidationError] = useState(null);
  const [inviteData, setInviteData] = useState(null);
  const [manualCode, setManualCode] = useState('');

  // Email & OTP steps
  const [emailInput, setEmailInput] = useState('');
  const [otpInput, setOtpInput] = useState('');
  const [step, setStep] = useState('email'); // 'email' | 'otp' | 'success'
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);
  const [resendTimer, setResendTimer] = useState(0);

  const validateToken = async (targetToken) => {
    const clean = (targetToken !== undefined ? targetToken : currentToken || token || '').trim();
    if (!clean || clean === 'manual') {
      setValidationError('Please enter an invitation code to claim your profile.');
      setValidating(false);
      return;
    }
    setValidating(true);
    setValidationError(null);
    try {
      const res = await profileService.validateInviteToken(clean);
      if (res && res.success) {
        setInviteData(res);
        if (res.token || res.invite_code) {
          setCurrentToken(res.token || res.invite_code || clean);
        }
        setValidationError(null);
      } else {
        setValidationError(res?.error || 'This invitation is invalid or has expired.');
      }
    } catch (err) {
      const isNetwork = (err?.message || '').toLowerCase().includes('fetch') || (err?.message || '').toLowerCase().includes('network');
      setValidationError(isNetwork ? 'Unable to reach FitLens service. Please verify your phone is connected to the same Wi-Fi network (192.168.0.107).' : (err.message || 'Error communicating with invitation service.'));
    } finally {
      setValidating(false);
    }
  };

  // 1. Validate opaque token on mount
  useEffect(() => {
    let isMounted = true;
    if (token && token !== 'manual') {
      validateToken(token);
    } else {
      setValidationError(null);
      setValidating(false);
    }
    return () => { isMounted = false; };
  }, [token]);

  // Resend cooldown timer
  useEffect(() => {
    if (resendTimer <= 0) return;
    const interval = setInterval(() => {
      setResendTimer(t => (t <= 1 ? 0 : t - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [resendTimer]);

  // Handle requesting 6-digit owner approval OTP
  const handleRequestOtp = async (e) => {
    e.preventDefault();
    setActionError(null);
    setActionSuccess(null);

    const trimmed = (emailInput || '').trim().toLowerCase();
    if (!trimmed || !trimmed.includes('@')) {
      setActionError('Please enter a valid owner email address.');
      return;
    }

    const tok = currentToken || token;
    setActionLoading(true);
    try {
      const res = await profileService.requestOwnerOtp(tok, trimmed);
      if (res.success) {
        setStep('otp');
        setActionSuccess("Approval code requested! A 6-digit code has been sent to the account owner's email address. Please ask the owner for the code.");
        setResendTimer(60);
      } else {
        setActionError(res.error || 'Unable to request approval code. Please verify the account owner email.');
      }
    } catch (err) {
      setActionError(err.message || 'Error requesting approval code.');
    } finally {
      setActionLoading(false);
    }
  };

  // Handle verifying owner OTP and unlocking profile
  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setActionError(null);
    setActionSuccess(null);

    const cleanOtp = (otpInput || '').trim();
    if (!cleanOtp || cleanOtp.length !== 6 || !/^\d+$/.test(cleanOtp)) {
      setActionError('Please enter the 6-digit approval code from the owner.');
      return;
    }

    const tok = currentToken || token;
    setActionLoading(true);
    try {
      const res = await profileService.verifyOwnerOtp(
        tok,
        emailInput.trim().toLowerCase(),
        cleanOtp,
        navigator.userAgent || 'Web Browser'
      );

      if (res.success && res.profile_session_token) {
        setStep('success');
        setActionSuccess(`✅ Owner approved! Unlocking "${res.profile?.name || 'My Profile'}"...`);
        setTimeout(() => {
          if (onClaimSuccess) {
            onClaimSuccess(res);
          }
        }, 700);
      } else {
        setActionError(res.error || 'Incorrect or expired approval code. Please check with the account owner.');
      }
    } catch (err) {
      setActionError(err.message || 'Error verifying approval code.');
    } finally {
      setActionLoading(false);
    }
  };

  // Resend OTP handler
  const handleResendOtp = async () => {
    if (resendTimer > 0 || actionLoading) return;
    setActionError(null);
    setActionLoading(true);
    const tok = currentToken || token;
    try {
      const res = await profileService.requestOwnerOtp(tok, emailInput.trim().toLowerCase());
      if (res.success) {
        setActionSuccess("A new 6-digit approval code was sent to the account owner's email.");
        setResendTimer(60);
      } else {
        setActionError(res.error || 'Could not resend code.');
      }
    } catch (err) {
      setActionError(err.message || 'Error resending code.');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0a0e27',
      backgroundImage: 'radial-gradient(circle at 50% 20%, rgba(30, 35, 64, 0.6) 0%, #0a0e27 80%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px 16px',
      fontFamily: 'Inter, system-ui, sans-serif',
      color: '#ffffff'
    }}>
      {/* Brand Header */}
      <div style={{ textAlign: 'center', marginBottom: '28px' }}>
        <img src={logo} alt="FitLens Logo" style={{ height: '90px', objectFit: 'contain', marginBottom: '10px' }} />
        <h1 style={{
          margin: '0 0 4px 0',
          fontSize: '24px',
          fontWeight: '800',
          letterSpacing: '-0.5px',
          color: '#ffffff'
        }}>
          FitLens Invitation
        </h1>
        <p style={{ margin: 0, color: '#a0aec0', fontSize: '14px' }}>
          Restricted Member Access • Secure Profile Space
        </p>
      </div>

      {/* Main Container Card */}
      <div style={{
        width: '100%',
        maxWidth: '520px',
        backgroundColor: '#1E2340',
        border: '1px solid #2D3561',
        borderRadius: '24px',
        padding: '32px',
        boxShadow: '0 24px 60px rgba(0, 0, 0, 0.55)',
        backdropFilter: 'blur(16px)',
        position: 'relative'
      }}>

        {/* Loading Token Validation State */}
        {validating && (
          <div style={{ textAlign: 'center', padding: '40px 10px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              margin: '0 auto 16px',
              border: '4px solid #2D3561',
              borderTop: '4px solid #00D4AA',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
            <h3 style={{ margin: '0 0 8px 0', color: '#00D4AA', fontSize: '18px' }}>
              Validating Invitation...
            </h3>
            <p style={{ margin: 0, color: '#a0aec0', fontSize: '13px' }}>
              Verifying one-time security token
            </p>
          </div>
        )}

        {/* State: Not Validating and No Valid Invite Loaded (Error OR Manual Entry) */}
        {!validating && !inviteData && (
          <div>
            {validationError ? (
              <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(239, 68, 68, 0.15)',
                  border: '2px solid #EF4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '30px',
                  margin: '0 auto 16px auto'
                }}>
                  ⚠️
                </div>
                <h3 style={{ margin: '0 0 10px 0', color: '#F87171', fontSize: '20px', fontWeight: '700' }}>
                  Invitation Unavailable
                </h3>
                <p style={{ color: '#cbd5e0', fontSize: '14px', lineHeight: '1.6', margin: '0 0 16px 0' }}>
                  {validationError}
                </p>

                {/* Retry Connection Button */}
                {currentToken && (
                  <button
                    type="button"
                    onClick={() => validateToken(currentToken)}
                    style={{
                      padding: '10px 20px',
                      backgroundColor: 'rgba(0, 212, 170, 0.15)',
                      border: '1px solid #00D4AA',
                      borderRadius: '10px',
                      color: '#00D4AA',
                      fontWeight: '700',
                      fontSize: '13px',
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      marginBottom: '8px',
                      transition: 'all 0.2s'
                    }}
                  >
                    🔄 Retry Connection
                  </button>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', marginBottom: '22px' }}>
                <div style={{
                  width: '60px',
                  height: '60px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(0, 212, 170, 0.15)',
                  border: '2px solid #00D4AA',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '28px',
                  margin: '0 auto 14px auto'
                }}>
                  🎟️
                </div>
                <h3 style={{ margin: '0 0 8px 0', color: '#ffffff', fontSize: '20px', fontWeight: '700' }}>
                  Claim Member Profile
                </h3>
                <p style={{ color: '#a0aec0', fontSize: '13px', margin: 0, lineHeight: '1.5' }}>
                  Enter the invitation code shared by the account owner to unlock your profile.
                </p>
              </div>
            )}

            {/* Manual Code Input Form (Always available on error or manual mode) */}
            <div style={{
              backgroundColor: '#0a0e27',
              border: '1px solid #2D3561',
              borderRadius: '16px',
              padding: '20px',
              marginBottom: '18px'
            }}>
              <label style={{
                display: 'block',
                fontSize: '12px',
                color: '#00D4AA',
                fontWeight: '700',
                letterSpacing: '1px',
                marginBottom: '8px',
                textTransform: 'uppercase'
              }}>
                {validationError ? 'Or Enter Invitation Code Manually' : 'Invitation Code'}
              </label>
              <form onSubmit={(e) => { e.preventDefault(); validateToken(manualCode); }} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <input
                  type="text"
                  value={manualCode}
                  onChange={(e) => setManualCode(e.target.value.toUpperCase())}
                  placeholder="e.g. FL-GH3W-6CL4"
                  autoCapitalize="characters"
                  spellCheck="false"
                  style={{
                    width: '100%',
                    padding: '14px 16px',
                    backgroundColor: '#1E2340',
                    border: '1px solid #2D3561',
                    borderRadius: '10px',
                    color: '#ffffff',
                    fontSize: '16px',
                    fontWeight: '700',
                    letterSpacing: '2px',
                    fontFamily: 'monospace',
                    textAlign: 'center',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
                <button
                  type="submit"
                  disabled={validating || !manualCode.trim()}
                  style={{
                    padding: '13px 20px',
                    backgroundColor: '#00D4AA',
                    border: 'none',
                    borderRadius: '10px',
                    color: '#0a0e27',
                    fontSize: '14px',
                    fontWeight: '800',
                    cursor: (validating || !manualCode.trim()) ? 'not-allowed' : 'pointer',
                    opacity: (!manualCode.trim() || validating) ? 0.6 : 1,
                    transition: 'all 0.2s',
                    boxShadow: '0 4px 14px rgba(0, 212, 170, 0.25)'
                  }}
                >
                  {validating ? 'Verifying Code...' : 'Validate Invitation Code'}
                </button>
              </form>
              <span style={{ fontSize: '11px', color: '#718096', marginTop: '10px', display: 'block', textAlign: 'center' }}>
                Found on the owner's screen directly under the QR code
              </span>
            </div>

            {/* Wi-Fi Connectivity & Security Notice Box */}
            <div style={{
              padding: '14px',
              backgroundColor: '#0a0e27',
              border: '1px solid #2D3561',
              borderRadius: '12px',
              color: '#a0aec0',
              fontSize: '12px',
              lineHeight: '1.6',
              textAlign: 'left',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <div>
                📶 <strong>Wi-Fi Network:</strong> Make sure this phone is connected to the same Wi-Fi network as the FitLens host server (<code style={{ color: '#00D4AA' }}>192.168.0.107</code>).
              </div>
              <div style={{ borderTop: '1px solid #1E2340', paddingTop: '8px' }}>
                🔒 <strong>Security Notice:</strong> Invitations are single-use and time-limited. If an invite has expired or already been claimed, ask the account owner for a fresh invitation.
              </div>
            </div>

            {/* Return to Home link */}
            <div style={{ marginTop: '22px', textAlign: 'center' }}>
              <button
                type="button"
                onClick={() => {
                  if (onCancel) {
                    onCancel();
                  } else {
                    window.location.href = window.location.pathname;
                  }
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#00D4AA',
                  fontSize: '13px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  textDecoration: 'underline'
                }}
              >
                ← Return to Home
              </button>
            </div>
          </div>
        )}

        {/* Valid Invitation Flow: Available Profiles in Restricted Mode */}
        {!validating && !validationError && inviteData && (
          <div>
            {/* Header Badge */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '20px',
              paddingBottom: '14px',
              borderBottom: '1px solid #2D3561'
            }}>
              <div>
                <span style={{
                  fontSize: '11px',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                  color: '#00D4AA',
                  fontWeight: '700'
                }}>
                  Restricted Mode
                </span>
                <h3 style={{ margin: '2px 0 0', fontSize: '18px', fontWeight: '800', color: '#ffffff' }}>
                  Available Profiles
                </h3>
              </div>
              <span style={{
                fontSize: '12px',
                padding: '4px 10px',
                backgroundColor: 'rgba(0, 212, 170, 0.15)',
                border: '1px solid #00D4AA',
                borderRadius: '12px',
                color: '#00D4AA',
                fontWeight: '700'
              }}>
                1 Assigned
              </span>
            </div>

            {/* Privacy Alert Banner */}
            <div style={{
              padding: '12px 14px',
              backgroundColor: 'rgba(0, 212, 170, 0.08)',
              border: '1px solid rgba(0, 212, 170, 0.25)',
              borderRadius: '12px',
              marginBottom: '20px',
              display: 'flex',
              gap: '10px',
              alignItems: 'flex-start'
            }}>
              <span style={{ fontSize: '18px' }}>🛡️</span>
              <p style={{ margin: 0, color: '#cbd5e0', fontSize: '12px', lineHeight: '1.5' }}>
                <strong style={{ color: '#00D4AA' }}>Privacy Isolated:</strong> Your personal body measurements, photos, and 3D mesh will remain strictly private to your assigned profile.
              </p>
            </div>

            {/* Profile Cards Section */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
              {/* 1. Assigned Profile Card (Highlighted with Lock) */}
              <div style={{
                backgroundColor: '#0a0e27',
                border: '2px solid #00D4AA',
                borderRadius: '16px',
                padding: '18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                boxShadow: '0 8px 24px rgba(0, 212, 170, 0.15)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <div style={{
                    width: '46px',
                    height: '46px',
                    borderRadius: '50%',
                    backgroundColor: 'rgba(0, 212, 170, 0.2)',
                    border: '1px solid #00D4AA',
                    color: '#00D4AA',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: '800',
                    fontSize: '18px'
                  }}>
                    {(inviteData.assigned_profile?.name || 'M').charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <strong style={{ color: '#ffffff', fontSize: '16px' }}>
                        {inviteData.assigned_profile?.name || 'Invited Member'}
                      </strong>
                      <span style={{
                        fontSize: '10px',
                        backgroundColor: '#2D3561',
                        color: '#a0aec0',
                        padding: '2px 8px',
                        borderRadius: '8px',
                        fontWeight: '700'
                      }}>
                        {inviteData.assigned_profile?.relationship || 'Member'}
                      </span>
                    </div>
                    <span style={{ color: '#a0aec0', fontSize: '12px', marginTop: '3px', display: 'block' }}>
                      🔒 Assigned to this invitation
                    </span>
                  </div>
                </div>

                <div style={{
                  padding: '6px 12px',
                  backgroundColor: 'rgba(255, 179, 0, 0.15)',
                  border: '1px solid #FFB300',
                  borderRadius: '10px',
                  color: '#FFB300',
                  fontSize: '12px',
                  fontWeight: '700',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <span>🔒 Locked</span>
                </div>
              </div>

              {/* 2. Anonymous Locked Placeholders for Other Profiles */}
              {inviteData.other_locked_profiles_count > 0 && (
                <div style={{
                  backgroundColor: 'rgba(10, 14, 39, 0.5)',
                  border: '1px dashed #2D3561',
                  borderRadius: '14px',
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  opacity: 0.75
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '18px', color: '#718096' }}>🔒</span>
                    <div>
                      <div style={{ fontSize: '13px', color: '#a0aec0', fontWeight: '600' }}>
                        Other profiles in this account
                      </div>
                      <div style={{ fontSize: '11px', color: '#718096' }}>
                        {inviteData.other_locked_profiles_count} profile{inviteData.other_locked_profiles_count > 1 ? 's' : ''} locked & non-interactive
                      </div>
                    </div>
                  </div>
                  <span style={{
                    fontSize: '11px',
                    color: '#718096',
                    backgroundColor: '#1E2340',
                    padding: '3px 8px',
                    borderRadius: '6px'
                  }}>
                    Inaccessible
                  </span>
                </div>
              )}
            </div>

            {/* Error & Success Feedback */}
            {actionError && (
              <div style={{
                padding: '12px 16px',
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid #EF4444',
                borderRadius: '12px',
                color: '#F87171',
                fontSize: '13px',
                marginBottom: '18px',
                lineHeight: '1.4'
              }}>
                ⚠️ {actionError}
              </div>
            )}

            {actionSuccess && (
              <div style={{
                padding: '12px 16px',
                backgroundColor: 'rgba(0, 212, 170, 0.15)',
                border: '1px solid #00D4AA',
                borderRadius: '12px',
                color: '#00D4AA',
                fontSize: '13px',
                marginBottom: '18px',
                lineHeight: '1.4'
              }}>
                {actionSuccess}
              </div>
            )}

            {/* Step 1: Owner Email Confirmation Input */}
            {step === 'email' && (
              <form onSubmit={handleRequestOtp} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ display: 'block', color: '#cbd5e0', fontSize: '12px', fontWeight: '700', marginBottom: '6px' }}>
                    ENTER ACCOUNT OWNER EMAIL
                  </label>
                  <input
                    type="email"
                    placeholder={`e.g. ${inviteData.masked_owner_email || inviteData.masked_email || 'owner@example.com'}`}
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    required
                    disabled={actionLoading}
                    style={{
                      width: '100%',
                      padding: '14px 16px',
                      backgroundColor: '#0a0e27',
                      border: '1px solid #2D3561',
                      borderRadius: '12px',
                      color: '#ffffff',
                      fontSize: '15px',
                      outline: 'none',
                      boxSizing: 'border-box'
                    }}
                  />
                  <span style={{ fontSize: '11px', color: '#a0aec0', marginTop: '6px', display: 'block', lineHeight: '1.4' }}>
                    Approval code will be sent to the owner's registered email: <strong style={{ color: '#00D4AA' }}>{inviteData.masked_owner_email || inviteData.masked_email}</strong>.
                    Ask the owner for the 6-digit code once requested.
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={actionLoading}
                  style={{
                    padding: '14px 20px',
                    backgroundColor: '#00D4AA',
                    border: 'none',
                    borderRadius: '12px',
                    color: '#0a0e27',
                    fontSize: '15px',
                    fontWeight: '800',
                    cursor: actionLoading ? 'wait' : 'pointer',
                    boxShadow: '0 4px 16px rgba(0, 212, 170, 0.3)',
                    marginTop: '4px',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {actionLoading ? 'Requesting Approval Code...' : '📨 Request Owner Approval'}
                </button>
              </form>
            )}

            {/* Step 2: 6-Digit Owner Approval OTP Verification Input */}
            {step === 'otp' && (
              <form onSubmit={handleVerifyOtp} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <label style={{ color: '#cbd5e0', fontSize: '12px', fontWeight: '700' }}>
                      6-DIGIT OWNER APPROVAL CODE
                    </label>
                    <button
                      type="button"
                      onClick={() => { setStep('email'); setActionError(null); }}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#00D4AA',
                        fontSize: '11px',
                        cursor: 'pointer',
                        textDecoration: 'underline'
                      }}
                    >
                      Change owner email
                    </button>
                  </div>

                  <input
                    type="text"
                    inputMode="numeric"
                    placeholder="••••••"
                    value={otpInput}
                    onChange={(e) => setOtpInput(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    maxLength={6}
                    required
                    autoFocus
                    disabled={actionLoading}
                    style={{
                      width: '100%',
                      padding: '14px 16px',
                      backgroundColor: '#0a0e27',
                      border: '1px solid #00D4AA',
                      borderRadius: '12px',
                      color: '#00D4AA',
                      fontSize: '26px',
                      fontWeight: '800',
                      letterSpacing: '10px',
                      textAlign: 'center',
                      fontFamily: 'monospace',
                      outline: 'none',
                      boxSizing: 'border-box'
                    }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
                    <span style={{ fontSize: '11px', color: '#a0aec0' }}>
                      Code sent to owner: <strong>{emailInput}</strong>
                    </span>
                    <button
                      type="button"
                      disabled={resendTimer > 0 || actionLoading}
                      onClick={handleResendOtp}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: resendTimer > 0 ? '#718096' : '#00D4AA',
                        fontSize: '11px',
                        fontWeight: '600',
                        cursor: resendTimer > 0 ? 'default' : 'pointer'
                      }}
                    >
                      {resendTimer > 0 ? `Resend code in ${resendTimer}s` : 'Resend code'}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={actionLoading}
                  style={{
                    padding: '14px 20px',
                    backgroundColor: '#00D4AA',
                    border: 'none',
                    borderRadius: '12px',
                    color: '#0a0e27',
                    fontSize: '15px',
                    fontWeight: '800',
                    cursor: actionLoading ? 'wait' : 'pointer',
                    boxShadow: '0 4px 16px rgba(0, 212, 170, 0.3)',
                    marginTop: '4px',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {actionLoading ? 'Verifying Approval Code...' : '🔓 Verify & Unlock Profile'}
                </button>
              </form>
            )}

            {/* Step 3: Success state */}
            {step === 'success' && (
              <div style={{ textAlign: 'center', padding: '20px 0' }}>
                <div style={{ fontSize: '36px', marginBottom: '8px' }}>🎉</div>
                <h3 style={{ margin: '0 0 6px', color: '#00D4AA' }}>Access Granted!</h3>
                <p style={{ margin: 0, color: '#a0aec0', fontSize: '13px' }}>
                  Entering your private measurement space...
                </p>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
