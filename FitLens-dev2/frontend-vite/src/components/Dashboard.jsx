import React, { useState } from 'react';
import UploadMode from './UploadMode';
import LiveCamera from './LiveCamera';
import './Dashboard.css';

const Dashboard = () => {
    const [mode, setMode] = useState(null); // 'upload' or 'live'

    const renderSelection = () => (
        <div className="dashboard-selection">
            <h2>Choose Measurement Mode</h2>
            <div className="mode-cards">
                <div className="mode-card" onClick={() => setMode('upload')}>
                    <div className="mode-icon">📤</div>
                    <h3>Upload Photos</h3>
                    <p>Upload existing photos for measurement</p>
                </div>

                <div className="mode-card" onClick={() => setMode('live')}>
                    <div className="mode-icon">📷</div>
                    <h3>Live Camera</h3>
                    <p>Real-time guidance and auto-capture</p>
                </div>
            </div>
        </div>
    );

    return (
        <div className="dashboard">
            {!mode && renderSelection()}

            {mode === 'upload' && (
                <div className="mode-container">
                    <button className="back-button" onClick={() => setMode(null)}>← Back to Menu</button>
                    <UploadMode />
                </div>
            )}

            {mode === 'live' && (
                <div className="mode-container">
                    <button className="back-button" onClick={() => setMode(null)}>← Back to Menu</button>
                    <LiveCamera />
                </div>
            )}
        </div>
    );
};

export default Dashboard;
