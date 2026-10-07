import React, { useState, useEffect } from 'react';
import UploadMode from './UploadMode';
import LiveCamera from './LiveCamera';
import { authHeaders, profileAuthHeaders } from '../services/authService';
import './Dashboard.css';

const Dashboard = ({ user, activeProfile, onLogout }) => {
    const [mode, setMode] = useState(null); // 'upload' or 'live'
    const [latestMeasurements, setLatestMeasurements] = useState(null);

    useEffect(() => {
        const fetchLatest = async () => {
            try {
                const pid = activeProfile?.profile_id || activeProfile?.id;
                const url = pid
                    ? `http://localhost:5000/api/profiles/${pid}/measurements/latest`
                    : 'http://localhost:5000/api/measurements/latest';
                const res = await fetch(url, {
                    headers: profileAuthHeaders()
                });
                const data = await res.json();
                if (data.success && data.latest) {
                    setLatestMeasurements(data.latest);
                } else {
                    setLatestMeasurements(null);
                }
            } catch (e) {
                console.warn('Could not fetch latest measurements:', e);
            }
        };
        fetchLatest();
    }, [activeProfile?.id, activeProfile?.profile_id]);

    const isOwner = Boolean(activeProfile?.is_owner || activeProfile?.profile_type === 'owner');

    const renderSelection = () => (
        <div className="dashboard-selection">
            {/* Active Profile Card */}
            <div
                style={{
                    backgroundColor: '#1E2340',
                    border: '1px solid #00D4AA',
                    borderRadius: '16px',
                    padding: '16px 20px',
                    marginBottom: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '12px',
                    boxShadow: '0 4px 16px rgba(0,212,170,0.15)',
                    textAlign: 'left'
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{
                        width: '42px',
                        height: '42px',
                        borderRadius: '50%',
                        backgroundColor: '#00D4AA',
                        color: '#0a0e27',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: '800',
                        fontSize: '18px',
                        flexShrink: 0
                    }}>
                        {(activeProfile?.name || user?.name || 'U').charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontSize: '12px', color: '#a0aec0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                Active Profile
                            </span>
                            <span style={{
                                fontSize: '11px',
                                backgroundColor: 'rgba(0, 212, 170, 0.2)',
                                color: '#00D4AA',
                                padding: '2px 8px',
                                borderRadius: '10px',
                                fontWeight: '700'
                            }}>
                                {activeProfile?.is_owner ? 'Owner' : (activeProfile?.relationship || 'Member')}
                            </span>
                        </div>
                        <h4 style={{ margin: '2px 0 0 0', color: '#ffffff', fontSize: '16px', fontWeight: '700' }}>
                            {activeProfile?.name || user?.name || 'Primary Profile'}
                        </h4>
                        <span style={{ fontSize: '12px', color: '#a0aec0' }}>
                            Default Height: <strong style={{ color: '#ffffff' }}>{activeProfile?.default_height_cm || 170} cm</strong> • Measurements taken are saved under this profile
                        </span>
                    </div>
                </div>
            </div>

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
                        📊 {activeProfile?.name ? `${activeProfile.name}'s` : 'Your'} last scan ({latestMeasurements.date})
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
                    <UploadMode user={user} activeProfile={activeProfile} />
                </div>
            )}

            {mode === 'live' && (
                <div className="mode-container">
                    <button className="back-button" onClick={() => setMode(null)}>← Back to Menu</button>
                    <LiveCamera user={user} activeProfile={activeProfile} />
                </div>
            )}
        </div>
    );
};

export default Dashboard;

