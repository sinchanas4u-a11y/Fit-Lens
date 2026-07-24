import React, { useState, useEffect } from 'react';
import UploadMode from './UploadMode';
import LiveCamera from './LiveCamera';
import { authHeaders } from '../services/authService';
import './Dashboard.css';

const Dashboard = ({ user, onLogout }) => {
    const [mode, setMode] = useState(null); // 'upload' or 'live'
    const [latestMeasurements, setLatestMeasurements] = useState(null);

    useEffect(() => {
        const fetchLatest = async () => {
            try {
                const res = await fetch('http://localhost:5000/api/measurements/latest', {
                    headers: authHeaders()
                });
                const data = await res.json();
                if (data.success && data.latest) {
                    setLatestMeasurements(data.latest);
                }
            } catch (e) {
                console.warn('Could not fetch latest measurements:', e);
            }
        };
        fetchLatest();
    }, []);

    const renderSelection = () => (
        <div className="dashboard-selection">
            {latestMeasurements && (
                <div className="previous-measurements-banner" style={{
                    backgroundColor: '#1E2340',
                    border: '1px solid #00D4AA',
                    borderRadius: '16px',
                    padding: '20px',
                    marginBottom: '28px',
                    textAlign: 'left',
                    color: '#ffffff',
                    boxShadow: '0 8px 24px rgba(0,212,170,0.15)'
                }}>
                    <h3 style={{ margin: '0 0 8px 0', color: '#00D4AA', fontSize: '18px' }}>
                        📊 Your last scan ({latestMeasurements.date})
                    </h3>
                    <p style={{ margin: '0 0 16px 0', color: '#e2e8f0', fontSize: '14px', lineHeight: '1.6' }}>
                        Height: {latestMeasurements.height_cm}cm | Arm: {latestMeasurements.arm_length}cm | Leg: {latestMeasurements.leg_length}cm | Shoulder: {latestMeasurements.shoulder_width}cm
                    </p>
                    <div style={{ display: 'flex', gap: '12px' }}>
                        <button
                            onClick={() => setMode('upload')}
                            style={{
                                padding: '10px 20px',
                                background: '#00D4AA',
                                border: 'none',
                                borderRadius: '10px',
                                color: '#0a0e27',
                                fontWeight: '700',
                                cursor: 'pointer',
                                fontSize: '14px'
                            }}
                        >
                            Use These Measurements
                        </button>
                        <button
                            onClick={() => setMode('upload')}
                            style={{
                                padding: '10px 20px',
                                background: '#2D3561',
                                border: 'none',
                                borderRadius: '10px',
                                color: '#ffffff',
                                fontWeight: '600',
                                cursor: 'pointer',
                                fontSize: '14px'
                            }}
                        >
                            Start New Scan
                        </button>
                    </div>
                </div>
            )}

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
                    <UploadMode user={user} />
                </div>
            )}

            {mode === 'live' && (
                <div className="mode-container">
                    <button className="back-button" onClick={() => setMode(null)}>← Back to Menu</button>
                    <LiveCamera user={user} />
                </div>
            )}
        </div>
    );
};

export default Dashboard;

