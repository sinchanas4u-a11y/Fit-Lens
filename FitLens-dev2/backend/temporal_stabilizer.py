"""
Temporal Stabilizer using RNN/LSTM
Ensures reference object and landmarks are stable over time
"""
import torch
import torch.nn as nn
import numpy as np
from collections import deque
from typing import Optional, List


class LSTMStabilizer(nn.Module):
    """LSTM model for temporal stability prediction"""
    
    def __init__(self, input_size: int = 4, hidden_size: int = 64, num_layers: int = 2):
        super(LSTMStabilizer, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        lstm_out, _ = self.lstm(x)
        # Take last output
        last_out = lstm_out[:, -1, :]
        out = self.fc(last_out)
        out = self.sigmoid(out)
        return out


class TemporalStabilizer:
    """Temporal stability checker using LSTM"""
    
    def __init__(self, sequence_length: int = 30, stability_threshold: float = 0.8):
        """
        Initialize temporal stabilizer
        
        Args:
            sequence_length: Number of frames to analyze
            stability_threshold: Threshold for stability score (0-1)
        """
        self.sequence_length = sequence_length
        self.stability_threshold = stability_threshold
        
        # Initialize LSTM model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = LSTMStabilizer().to(self.device)
        self.model.eval()
        
        # Buffers for temporal data
        self.reference_buffer = deque(maxlen=sequence_length)
        self.landmark_buffer = deque(maxlen=sequence_length)
        
        # Reference baseline
        self.reference_baseline = None
    
    def initialize_reference(self, frame: np.ndarray, ref_size: float):
        """Initialize reference baseline"""
        self.reference_baseline = ref_size
        self.reference_buffer.clear()
    
    def check_reference_stability(self, frame: np.ndarray) -> bool:
        """
        Check if reference object is stable
        
        Args:
            frame: Current frame
            
        Returns:
            True if reference is stable
        """
        if self.reference_baseline is None:
            return False
        
        # Detect current reference (simplified)
        # In practice, use reference_detector here
        current_ref = self.reference_baseline  # Placeholder
        
        # Add to buffer
        self.reference_buffer.append(current_ref)
        
        if len(self.reference_buffer) < self.sequence_length:
            return False
        
        # Calculate stability score
        stability_score = self._calculate_stability(list(self.reference_buffer))
        
        return stability_score > self.stability_threshold
    
    def check_landmark_stability(self, landmarks: np.ndarray) -> bool:
        """
        Check if landmarks are stable
        
        Args:
            landmarks: Detected landmarks
            
        Returns:
            True if landmarks are stable
        """
        if landmarks is None:
            return False
        
        # Extract key features (e.g., center of mass, variance)
        features = self._extract_landmark_features(landmarks)
        
        # Add to buffer
        self.landmark_buffer.append(features)
        
        if len(self.landmark_buffer) < self.sequence_length:
            return False
        
        # Calculate stability
        stability_score = self._calculate_stability(list(self.landmark_buffer))
        
        return stability_score > self.stability_threshold
    
    def _extract_landmark_features(self, landmarks: np.ndarray) -> np.ndarray:
        """Extract features from landmarks for stability check"""
        # Calculate center of mass
        center_x = np.mean(landmarks[:, 0])
        center_y = np.mean(landmarks[:, 1])
        
        # Calculate variance
        var_x = np.var(landmarks[:, 0])
        var_y = np.var(landmarks[:, 1])
        
        return np.array([center_x, center_y, var_x, var_y])
    
    def _calculate_stability(self, sequence: List) -> float:
        """
        Calculate stability score using LSTM
        
        Args:
            sequence: Temporal sequence of measurements
            
        Returns:
            Stability score (0-1)
        """
        # Convert to tensor
        seq_array = np.array(sequence)
        
        # Handle different input shapes
        if seq_array.ndim == 1:
            seq_array = seq_array.reshape(-1, 1)
        
        # Pad to 4 features if needed
        if seq_array.shape[1] < 4:
            padding = np.zeros((seq_array.shape[0], 4 - seq_array.shape[1]))
            seq_array = np.hstack([seq_array, padding])
        
        # Convert to tensor
        seq_tensor = torch.FloatTensor(seq_array).unsqueeze(0).to(self.device)
        
        # Get prediction
        with torch.no_grad():
            stability_score = self.model(seq_tensor).item()
        
        return stability_score
    
    def smooth_landmarks(self, landmarks: np.ndarray) -> np.ndarray:
        """
        Apply temporal smoothing to landmarks
        
        Args:
            landmarks: Current landmarks
            
        Returns:
            Smoothed landmarks
        """
        if len(self.landmark_buffer) == 0:
            return landmarks
        
        # Simple moving average smoothing
        recent_landmarks = list(self.landmark_buffer)[-5:]  # Last 5 frames
        
        if len(recent_landmarks) > 0:
            # Average the landmarks
            smoothed = np.mean([lm for lm in recent_landmarks], axis=0)
            return smoothed
        
        return landmarks
    
    def reset(self):
        """Reset all buffers"""
        self.reference_buffer.clear()
        self.landmark_buffer.clear()
        self.reference_baseline = None
