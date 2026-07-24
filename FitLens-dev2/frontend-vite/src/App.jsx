import { useState } from 'react'
import Dashboard from './components/Dashboard'
import logo from './assets/logo.png'
import './App.css'

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', marginBottom: '8px' }}>
          <img src={logo} alt="FitLens Logo" style={{ height: '80px', objectFit: 'contain' }} />
        </div>
        <h2>Body Measurement System</h2>
        <p>YOLOv8 Segmentation + MediaPipe Landmarks + SMPL 3D Mesh</p>
      </header>

      <main>
        <Dashboard />
      </main>

      <footer className="App-footer">
        <p></p>
      </footer>
    </div>
  )
}

export default App
