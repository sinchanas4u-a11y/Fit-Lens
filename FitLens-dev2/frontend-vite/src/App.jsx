import { useState } from 'react'
import Dashboard from './components/Dashboard'
import './App.css'

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Body Measurement System</h1>
        <p>YOLOv8 Segmentation + MediaPipe Landmarks</p>
      </header>

      <main>
        <Dashboard />
      </main>

      <footer className="App-footer">
        <p>Powered by YOLOv8 and MediaPipe</p>
      </footer>
    </div>
  )
}

export default App
