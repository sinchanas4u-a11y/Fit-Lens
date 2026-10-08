import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import LoginScreen from './components/LoginScreen'
import ResetPasswordScreen from './components/ResetPasswordScreen'
import SettingsScreen from './components/SettingsScreen'
import ProfileSelectionModal from './components/ProfileSelectionModal'
import ClaimInviteModal from './components/ClaimInviteModal'
import InviteClaimScreen from './components/InviteClaimScreen'
import MyProfileModal from './components/MyProfileModal'
import { isLoggedIn, removeToken, getCurrentUser, clearAllAuthSessions, getAccessMode } from './services/authService'
import { profileService } from './services/profileService'
import logo from './assets/logo.png'
import './App.css'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showSettings, setShowSettings] = useState(false)
  const [settingsTab, setSettingsTab] = useState('profile')
  const [showMyProfile, setShowMyProfile] = useState(false)

  // Multi-Profile State
  const [activeProfile, setActiveProfile] = useState(() => profileService.getActiveProfile())
  const [profiles, setProfiles] = useState([])
  const [slotUsage, setSlotUsage] = useState({ active_count: 1, max_slots: 4 })
  const [showProfileSelector, setShowProfileSelector] = useState(false)
  const [loginMemberEmail, setLoginMemberEmail] = useState('')

  const [inviteToken, setInviteToken] = useState(() => {
    const sp = new URLSearchParams(window.location.search);
    if (sp.get('invite_token')) return sp.get('invite_token');
    if (sp.get('invite_code')) return sp.get('invite_code');
    if (!window.location.pathname.includes('reset') && !sp.has('reset') && sp.get('token')) return sp.get('token');
    return null;
  });
  const isResetPasswordPath = window.location.pathname === '/reset-password' || (!inviteToken && new URLSearchParams(window.location.search).has('token'));
  const [claimInviteCode, setClaimInviteCode] = useState(null);

  const loadProfiles = async () => {
    try {
      // First try getAvailableProfiles which works for both owner and invited non-owners
      let data = await profileService.getAvailableProfiles()
      if (!data.success || !data.profiles) {
        data = await profileService.listProfiles()
      }
      if (data.success && data.profiles) {
        setProfiles(data.profiles)
        setSlotUsage({
          active_count: data.active_profiles_count ?? data.profiles.length,
          pending_count: data.pending_invites_count ?? 0,
          max_slots: data.max_allowed_slots ?? 4
        })
        const saved = profileService.getActiveProfile()
        const found = saved ? data.profiles.find(p => (p.id || p.profile_id) === (saved.id || saved.profile_id)) : null
        if (found) {
          setActiveProfile(found)
        }
        return data.profiles
      }
    } catch (err) {
      console.warn('Could not load profiles in App:', err)
    }
    return []
  }

  useEffect(() => {
    const checkAuth = async () => {
      if (isLoggedIn()) {
        const currentUser = await getCurrentUser()
        if (currentUser) {
          setUser(currentUser)
          const loadedProfiles = await loadProfiles()
          const saved = profileService.getActiveProfile()
          if (saved) {
            setActiveProfile(saved)
            if (getAccessMode() === 'invited_profile') {
              setProfiles([saved])
              setShowProfileSelector(false)
            }
          } else if (loadedProfiles.length > 0) {
            if (getAccessMode() === 'invited_profile') {
              setActiveProfile(loadedProfiles[0])
              profileService.saveActiveProfile(loadedProfiles[0])
              setShowProfileSelector(false)
            } else {
              setShowProfileSelector(true)
            }
          }
        } else {
          clearAllAuthSessions()
        }
      }
      setLoading(false)
    }
    checkAuth()
  }, [])

  const handleLogout = () => {
    clearAllAuthSessions()
    setUser(null)
    setActiveProfile(null)
    setShowSettings(false)
    setShowProfileSelector(false)
  }

  const handleLoginSuccess = async (u, memberEmail = '') => {
    setUser(u)
    setLoginMemberEmail(memberEmail || '')
    profileService.saveActiveProfile(null)
    profileService.clearUnlockedProfileId()
    setActiveProfile(null)
    await loadProfiles()
    setShowProfileSelector(true) // Always show profile selection immediately upon login!
  }

  if (isResetPasswordPath) {
    return <ResetPasswordScreen onResetSuccess={() => { window.location.href = '/'; }} />
  }

  // Non-owner member invitation flow:
  // Non-owner opens link or scans QR -> NEVER show owner login page!
  if (inviteToken) {
    return (
      <InviteClaimScreen
        token={inviteToken}
        onCancel={() => {
          window.history.replaceState({}, '', window.location.pathname);
          setInviteToken(null);
        }}
        onClaimSuccess={async (claimRes) => {
          window.history.replaceState({}, '', window.location.pathname);
          setInviteToken(null);
          setClaimInviteCode(null);
          try {
            if (claimRes?.profile) {
              const p = claimRes.profile;
              setActiveProfile(p);
              profileService.saveActiveProfile(p);
              profileService.saveUnlockedProfileId(p.id || p.profile_id);
              setProfiles([p]);
              setUser(claimRes.user || {
                name: p.name,
                role: 'profile_member_session',
                access_mode: 'invited_profile'
              });
              setShowProfileSelector(false);
              setShowSettings(false);
            } else {
              await loadProfiles();
            }
          } catch (err) {
            console.error('Error completing claim in App:', err);
          }
        }}
      />
    );
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: '#0a0e27', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#00D4AA' }}>
        <h3>Loading FitLens...</h3>
      </div>
    )
  }

  if (!user && !isLoggedIn()) {
    return (
      <>
        <LoginScreen
          onLoginSuccess={handleLoginSuccess}
          onClaimInviteClick={() => setInviteToken('manual')}
        />
        {claimInviteCode && (
          <ClaimInviteModal
            initialCode={claimInviteCode}
            onClose={() => {
              setClaimInviteCode(null);
              window.history.replaceState({}, '', window.location.pathname);
            }}
            onClaimSuccess={async (claimRes) => {
              setClaimInviteCode(null);
              window.history.replaceState({}, '', window.location.pathname);
              if (claimRes?.profile) {
                const p = claimRes.profile;
                setActiveProfile(p);
                profileService.saveActiveProfile(p);
                profileService.saveUnlockedProfileId(p.id || p.profile_id);
                setProfiles([p]);
                setUser(claimRes.user || {
                  name: p.name,
                  role: 'profile_member_session',
                  access_mode: 'invited_profile'
                });
                setShowProfileSelector(false);
                setShowSettings(false);
              } else {
                await loadProfiles();
              }
            }}
          />
        )}
      </>
    )
  }

  return (
    <div className="App">
      <header className="App-header" style={{ position: 'relative' }}>
        <div style={{ position: 'absolute', top: '16px', right: '20px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px', zIndex: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ color: '#00D4AA', fontWeight: 'bold', fontSize: '14px' }}>
              👤 Welcome back, {user?.name || 'User'} 👋
            </span>
            {getAccessMode() === 'invited_profile' ? (
              <button
                onClick={() => setShowMyProfile(true)}
                style={{
                  padding: '6px 14px',
                  backgroundColor: '#1E2340',
                  border: '1px solid #00D4AA',
                  color: '#00D4AA',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '13px'
                }}
              >
                👤 My Profile
              </button>
            ) : (
              <button
                onClick={() => {
                  setSettingsTab('profile');
                  setShowSettings(!showSettings);
                }}
                style={{
                  padding: '6px 14px',
                  backgroundColor: '#1E2340',
                  border: '1px solid #2D3561',
                  color: '#00D4AA',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '13px'
                }}
              >
                ⚙️ Settings
              </button>
            )}
            <button
              onClick={handleLogout}
              style={{
                padding: '6px 14px',
                backgroundColor: '#1E2340',
                border: '1px solid #2D3561',
                color: '#fc8181',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '13px'
              }}
            >
              Logout 🚪
            </button>
          </div>

          {/* Active Profile Chip below Welcome back, User 👋 */}
          {user && (
            <div
              onClick={() => {
                if (getAccessMode() === 'invited_profile') {
                  setShowMyProfile(true);
                }
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                backgroundColor: '#1E2340',
                border: '1px solid #00D4AA',
                borderRadius: '20px',
                padding: '4px 12px 4px 6px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
                cursor: getAccessMode() === 'invited_profile' ? 'pointer' : 'default'
              }}
              title={getAccessMode() === 'invited_profile' ? 'Click to edit your personal details' : undefined}
            >
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                backgroundColor: '#00D4AA',
                color: '#0a0e27',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: '800',
                fontSize: '12px'
              }}>
                {(activeProfile?.name || user?.name || 'U').charAt(0).toUpperCase()}
              </div>
              <span style={{ fontSize: '12px', color: '#a0aec0' }}>Active Profile:</span>
              <strong style={{ fontSize: '13px', color: '#ffffff' }}>
                {activeProfile?.name || user?.name || 'Primary'}
              </strong>
              <span style={{
                fontSize: '10px',
                backgroundColor: 'rgba(0, 212, 170, 0.2)',
                color: '#00D4AA',
                padding: '2px 6px',
                borderRadius: '8px',
                fontWeight: '700'
              }}>
                {activeProfile?.is_owner ? 'Owner' : (activeProfile?.relationship || 'Member')}
              </span>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', marginBottom: '8px' }}>
          <img src={logo} alt="FitLens Logo" style={{ height: '120px', objectFit: 'contain' }} />
        </div>
        <h2>Body Measurement System</h2>
        <p>YOLOv8 Segmentation + MediaPipe Landmarks + SMPL 3D Mesh</p>
      </header>

      <main>
        {showSettings && getAccessMode() !== 'invited_profile' ? (
          <SettingsScreen
            user={user}
            initialTab={settingsTab}
            activeProfile={activeProfile}
            onActiveProfileChanged={(p) => {
              setActiveProfile(p);
              profileService.saveActiveProfile(p);
              loadProfiles();
            }}
            onUserUpdated={(u) => setUser(u)}
            onLogout={handleLogout}
            onClose={() => {
              setShowSettings(false);
              setSettingsTab('profile');
            }}
          />
        ) : (
          <Dashboard
            user={user}
            activeProfile={activeProfile}
            onLogout={handleLogout}
          />
        )}
      </main>

      {/* Non-owner Member Self-Service Edit Modal */}
      <MyProfileModal
        isOpen={showMyProfile}
        activeProfile={activeProfile}
        onProfileUpdated={(updated) => {
          setActiveProfile(updated);
          profileService.saveActiveProfile(updated);
        }}
        onClose={() => setShowMyProfile(false)}
      />

      {claimInviteCode && (
        <ClaimInviteModal
          initialCode={claimInviteCode}
          onClose={() => {
            setClaimInviteCode(null);
            window.history.replaceState({}, '', window.location.pathname);
            loadProfiles();
          }}
          onClaimSuccess={() => {
            loadProfiles();
          }}
        />
      )}

      {/* Available Profiles Modal: Select & Unlock Profiles */}
      {getAccessMode() !== 'invited_profile' && (
        <ProfileSelectionModal
          isOpen={showProfileSelector}
          profiles={profiles}
          user={user}
          initialMemberEmail={loginMemberEmail}
          onSelectProfile={(profile) => {
            setActiveProfile(profile);
            profileService.saveActiveProfile(profile);
            setShowProfileSelector(false);
          }}
          onLogout={handleLogout}
        />
      )}

      <footer className="App-footer">
        <p></p>
      </footer>
    </div>
  )
}

export default App


