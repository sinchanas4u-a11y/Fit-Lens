import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import Dashboard from './components/Dashboard';
import UploadMode from './components/UploadMode';
import LiveMode from './components/LiveMode';
import './App.css';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#4caf50',
    },
  },
});

function App() {
  const [mode, setMode] = useState(null);

  const handleModeSelect = (selectedMode) => {
    setMode(selectedMode);
  };

  const handleBack = () => {
    setMode(null);
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Container maxWidth="xl" className="app-container">
        {mode === null && <Dashboard onModeSelect={handleModeSelect} />}
        {mode === 'upload' && <UploadMode onBack={handleBack} />}
        {mode === 'live' && <LiveMode onBack={handleBack} />}
      </Container>
    </ThemeProvider>
  );
}

export default App;
