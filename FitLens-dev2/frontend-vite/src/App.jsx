import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import LoginScreen from './components/LoginScreen'
import ResetPasswordScreen from './components/ResetPasswordScreen'
import SettingsScreen from './components/SettingsScreen'
import { isLoggedIn, removeToken, getCurrentUser } from './services/authService'
import logo from './assets/logo.png'
import './App.css'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showSettings, setShowSettings] = useState(false)

  const isResetPasswordPath = window.location.pathname === '/reset-password' || new URLSearchParams(window.location.search).has('token')

  useEffect(() => {
    const checkAuth = async () => {
      if (isLoggedIn()) {
        const currentUser = await getCurrentUser()
        if (currentUser) {
          setUser(currentUser)
        } else {
          removeToken()
        }
      }
      setLoading(false)
    }
    checkAuth()
  }, [])

  const handleLogout = () => {
    removeToken()
    localStorage.removeItem('fitlens_user')
    setUser(null)
    setShowSettings(false)
  }

  if (isResetPasswordPath) {
    return <ResetPasswordScreen onResetSuccess={() => { window.location.href = '/'; }} />
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: '#0a0e27', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#00D4AA' }}>
        <h3>Loading FitLens...</h3>
      </div>
    )
  }

  if (!user && !isLoggedIn()) {
    return <LoginScreen onLoginSuccess={(u) => setUser(u)} />
  }

  return (
    <div className="App">
      <header className="App-header" style={{ position: 'relative' }}>
        <div style={{ position: 'absolute', top: '20px', right: '20px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ color: '#00D4AA', fontWeight: 'bold', fontSize: '14px' }}>
            👤 Welcome, {user?.name || 'User'}
          </span>
          <button
            onClick={() => setShowSettings(!showSettings)}
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

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', marginBottom: '8px' }}>
          <img src={logo} alt="FitLens Logo" style={{ height: '120px', objectFit: 'contain' }} />
        </div>
        <h2>Body Measurement System</h2>
        <p>YOLOv8 Segmentation + MediaPipe Landmarks + SMPL 3D Mesh</p>
      </header>

      <main>
        {showSettings ? (
          <SettingsScreen
            user={user}
            onUserUpdated={(u) => setUser(u)}
            onLogout={handleLogout}
            onClose={() => setShowSettings(false)}
          />
        ) : (
          <Dashboard user={user} onLogout={handleLogout} />
        )}
      </main>

      <footer className="App-footer">
        <p></p>
      </footer>
    </div>
  )
}

export default App


