import { useState } from 'react'
import Dashboard from './components/Dashboard'
import './App.css'

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>FitLens AI 📏</h1>
        <h2>Body Measurement System</h2>
        <p>YOLOv8 Segmentation + MediaPipe Landmarks</p>
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
